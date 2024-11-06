import cv2
import numpy as np
import time
import os
import csv
import asyncio
import gc
from ultralytics import YOLO

# Load the YOLO model
# model = YOLO('blue_brown_box.pt')
model = YOLO('blue_brown_box.pt').to('cuda').half()

# Define the RTSP video path
video_path = "rtmp://localhost/live/stream4?rtsp_transport=tcp&fflags=+igndts&flags=low_delay"

# Prepare folder and log file
current_datetime = time.strftime('%Y-%m-%d_%H-%M-%S')
log_folder = f"logs_11_no_re/{current_datetime}"
os.makedirs(log_folder, exist_ok=True)
log_file = f"{log_folder}/monitoringlog11_{current_datetime}.csv"

# Initialize CSV logging
async def init_log():
    with open(log_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Timestamp", "Event", "Frame Number", "Details"])
        writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), "Stream Started", "", ""])

# Log events for missed and processed frames
async def log_event(event, frame_number="", details=""):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, event, frame_number, details])

# Log errors
async def log_error(error_message, frame_number=""):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, "Error", frame_number, error_message])

# Set up video writer
def setup_video_writer(width, height, fps=25):
    output_file = "detection_output_bindhu111.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    return cv2.VideoWriter(output_file, fourcc, fps, (width, height))

# Zone and class detection
ZONE_COORDINATES = np.array([(150, 4), (220, 5), (220, 283), (150, 280)], np.int32)
zone_counts = {"blue_box": 0, "brown_box": 0}
recent_frames = set()  # Track processed frames within a window
detected_count = 0  # Global variable for total detected count

def is_frame_recent(frame_index, recent_frames):
    return any(frame_index - i < 20 for i in recent_frames)

def update_zone_counts(class_name):
    global detected_count  # Access the global detected_count
    if class_name == 'blue_box' or class_name == 'brown_box':
        detected_count += 1  # Increment the detected count

# Process each frame with yield
async def process_frame(frame, frame_index, video_writer):
    try:
        results = model(frame)
        for result in results:
            for box in result.boxes:
                if box.conf >= 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    class_id = int(box.cls)
                    class_name = model.names[class_id]

                    centroid_x, centroid_y = (x1 + x2) // 2, (y1 + y2) // 2
                    if (x2 - x1 > 5 and y2 - y1 > 5) and cv2.pointPolygonTest(ZONE_COORDINATES, (centroid_x, centroid_y), False) >= 0:
                        if not is_frame_recent(frame_index, recent_frames):
                            recent_frames.add(frame_index)
                            update_zone_counts(class_name)

                    # Draw bounding box and centroid
                    color = (255, 255, 0) if class_name == 'blue_box' else (255, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.circle(frame, (centroid_x, centroid_y), 5, color, -1)

        cv2.polylines(frame, [ZONE_COORDINATES], isClosed=True, color=(0, 255, 0), thickness=2)
        display_counts(frame, frame_index)
        video_writer.write(frame)

    except Exception as e:
        await log_error(f"Error processing frame {frame_index}: {str(e)}", frame_index)

def display_counts(frame, frame_index):
    # Display the counts and detected count
    cv2.putText(frame, f"FRAME_COUNT: {frame_index}", (100, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(frame, f"Detected Count: {detected_count}", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

# Capture video frames with yield
async def video_capture_loop(video_writer):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    frame_index = 0
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
    frames_to_skip = 10 # Skip 5 frames each second

    while cap.isOpened():
        try:
            ret, frame = cap.read()
            if not ret:
                await log_event("Missed Frame", frame_index)
                break

            # Only process every (fps / frames_to_skip)th frame per second
            if frame_index % (fps // frames_to_skip) != 0:
                frame_index += 1
                continue

            # Process and log the frame asynchronously
            await log_event("Processed Frame", frame_index)
            await process_frame(frame, frame_index, video_writer)

            # Display resized output
            disp = cv2.resize(frame, (800, 800))
            cv2.imshow('Object Detectionss', disp)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Increment frame index and yield control to free up resources
            frame_index += 1
            if frame_index % 50 == 0:  # Call garbage collection every 50 frames
                gc.collect()
            await asyncio.sleep(0)  # Yield control

        except Exception as e:
            await log_error(f"Error in video capture loop: {str(e)}", frame_index)
            break

    # Finalize log and cleanup
    await log_event("Stream Ended", frame_index)
    await log_event("Total Frames Processed", frame_index)
    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()

async def main():
    await init_log()
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
    width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    video_writer = setup_video_writer(width, height, fps)
    await video_capture_loop(video_writer)

if __name__ == "__main__":
    asyncio.run(main())
