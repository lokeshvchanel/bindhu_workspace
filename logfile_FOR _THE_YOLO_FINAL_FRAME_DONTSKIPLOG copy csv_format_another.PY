# import cv2
# import numpy as np
# import time
# from collections import deque
# import csv
# from ultralytics import YOLO

# # Load the YOLO model
# model = YOLO('blue_brown_box.pt')

# # Define the RTSP video path with additional FFmpeg options
# video_path = (
#     "rtmp://localhost/live/stream"
#     "?rtsp_transport=tcp&fflags=+igndts&flags=low_delay"
# )

# # Set up connection parameters
# reconnection_attempts = 1  # Max number of reconnection attempts
# reconnection_delay = 0.5  # Delay (in seconds) between reconnection attempts
# missed_frame_count = 0  # Counter for missed frames

# # CSV file for logging
# log_file = "monitoringlog.csv"

# # Initialize CSV logging
# with open(log_file, 'w', newline='') as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerow(["Timestamp", "Event", "Frame Number", "Details"])  # CSV headers
#     # Log stream start time
#     start_time = time.strftime('%Y-%m-%d %H:%M:%S')
#     writer.writerow([start_time, "Stream Started", "", ""])

# def log_missed_frame(frame_number):
#     """Log missed frame details to CSV file."""
#     global missed_frame_count
#     missed_frame_count += 1
#     timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
#     with open(log_file, 'a', newline='') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow([timestamp, "Missed Frame", frame_number, ""])

# def log_processed_frame(frame_number):
#     """Log processed frame details to CSV file."""
#     timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
#     with open(log_file, 'a', newline='') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow([timestamp, "Processed Frame", frame_number, ""])

# def create_video_capture():
#     cap = cv2.VideoCapture(video_path)
#     cap.set(cv2.CAP_PROP_BUFFERSIZE, 38)
#     return cap

# cap = create_video_capture()

# # Get video properties
# fps = int(cap.get(cv2.CAP_PROP_FPS)) #or 25  # Default to 25 fps if fps is not available
# width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# # Define the zone coordinates
# zone = [(150, 4), (220, 5), (220, 283), (150, 280)]

# # Initialize counters for different classes
# chain_box_count = 0
# rect_box_count = 0
# recent_frames = []

# # Buffer for frames
# frame_buffer = deque(maxlen=30)  # Buffer for storing recent frames

# # Function to check if a frame is recent
# def is_frame_recent(frame_index, recent_frames):
#     return any(frame_index - i < 20 for i in recent_frames)

# frame_index = 0
# drop_count = 0

# while True:
#     ret, frame = cap.read()

#     # Attempt to reconnect on failed frame read
#     if not ret:
#         print("Frame dropped. Retrying...")
#         drop_count += 1
#         log_missed_frame(frame_index)  # Log the missed frame

#         # Reconnect if drop count exceeds threshold
#         if drop_count > 5:
#             cap.release()
#             print("Attempting to reconnect to stream...")

#             for attempt in range(reconnection_attempts):
#                 cap = create_video_capture()
#                 time.sleep(reconnection_delay)  # Wait briefly before trying to read a frame

#                 # Test if reconnection was successful
#                 if cap.isOpened() and cap.read()[0]:  # Check if the stream is available
#                     print("Reconnected successfully.")
#                     drop_count = 0
#                     break
#             else:
#                 print("Failed to reconnect after multiple attempts.")
#                 break
#         continue

#     # Reset drop count on successful frame read
#     drop_count = 0

#     # Log the current frame index
#     log_processed_frame(frame_index)

#     # Add the current frame to the buffer
#     frame_buffer.append((frame, frame_index))

#     # Process frames from the buffer
#     while frame_buffer:
#         current_frame, index = frame_buffer.popleft()

#         # Perform object detection on the frame
#         results = model(current_frame)

#         # Draw bounding boxes and centroids on detected objects with confidence >= 0.5
#         for result in results:
#             for box in result.boxes:
#                 if box.conf >= 0.5:
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])
#                     class_id = int(box.cls)
#                     class_name = model.names[class_id]

#                     width = x2 - x1
#                     height = y2 - y1

#                     # Draw the bounding box
#                     cv2.rectangle(current_frame, (x1, y1), (x2, y2), (0, 255, 255), 1)

#                     # Calculate and draw the centroid
#                     centroid_x = int((x1 + x2) / 2)
#                     centroid_y = int((y1 + y2) / 2)
#                     cv2.circle(current_frame, (centroid_x, centroid_y), 5, (255, 255, 0), -1)

#                     # Check if the bounding box size is greater than 5x5
#                     if width > 5 and height > 5:
#                         if cv2.pointPolygonTest(np.array(zone, np.int32), (centroid_x, centroid_y), False) >= 0:
#                             if not is_frame_recent(index, recent_frames):
#                                 recent_frames.append(index)

#                                 # Count objects in zone based on class name
#                                 if class_name == 'blue_box':
#                                     chain_box_count += 1
#                                     cv2.rectangle(current_frame, (x1, y1), (x2, y2), (255, 255, 0), 5)
#                                 elif class_name == 'brown_box':
#                                     rect_box_count += 1
#                                     cv2.rectangle(current_frame, (x1, y1), (x2, y2), (255, 0, 255), 5)

#         # Draw the zone bounding box
#         cv2.polylines(current_frame, [np.array(zone, np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)
#         cv2.putText(current_frame, f"FRAME_COUNT: {frame_index}", (100, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

#         # Display the count for chain_box and rect_box
#         cv2.putText(current_frame, f"Box Count A: {chain_box_count}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
#         cv2.putText(current_frame, f"Box Count B: {rect_box_count}", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 250), 3)

#         # Resize and display the frame
#         disp = cv2.resize(current_frame, (800, 800))
#         cv2.imshow('Object Detection', disp)

#         # Save the current frame when 's' is pressed
#         if cv2.waitKey(1) & 0xFF == ord('s'):
#             frame_filename = f"saved_frame_{index}.png"
#             cv2.imwrite(frame_filename, current_frame)
#             print(f"Frame saved: {frame_filename}")

#     # Increment the frame index
#     frame_index += 1

#     # Break the loop if 'q' is pressed
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Log stream end time and missed frames
# end_time = time.strftime('%Y-%m-%d %H:%M:%S')
# with open(log_file, 'a', newline='') as csvfile:
#     writer = csv.writer(csvfile)
#     writer.writerow([end_time, "Stream Ended", "", ""])
#     writer.writerow(["", "Total Frames Processed", frame_index, ""])
#     writer.writerow(["", "Total Missed Frames", missed_frame_count, ""])

# # Release resources
# cap.release()
# cv2.destroyAllWindows()



import cv2
import numpy as np
import time
from collections import deque
import csv
from ultralytics import YOLO

# Load the YOLO model
model = YOLO('blue_brown_box.pt')

# Define the RTSP video path with additional FFmpeg options
video_path = (
    "rtmp://localhost/live/stream4"
    "?rtsp_transport=tcp&fflags=+igndts&flags=low_delay"
)

# Set up connection parameters
reconnection_attempts = 1  # Max number of reconnection attempts
reconnection_delay = 0.5  # Delay (in seconds) between reconnection attempts
missed_frame_count = 0  # Counter for missed frames

# CSV file for logging
log_file = "monitoringlog1.csv"

# Initialize CSV logging
with open(log_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Timestamp", "Event", "Frame Number", "Details"])  # CSV headers
    start_time = time.strftime('%Y-%m-%d %H:%M:%S')
    writer.writerow([start_time, "Stream Started", "", ""])

def log_missed_frame(frame_number):
    global missed_frame_count
    missed_frame_count += 1
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, "Missed Frame", frame_number, ""])

def log_processed_frame(frame_number):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([timestamp, "Processed Frame", frame_number, ""])

def create_video_capture():
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 38)
    return cap

cap = create_video_capture()

# Get video properties
fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Initialize VideoWriter to save output video
output_file = "detection_output_bindhu.mp4"
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

# Define the zone coordinates
zone = [(150, 4), (220, 5), (220, 283), (150, 280)]

# Initialize counters for different classes
chain_box_count = 0
rect_box_count = 0
recent_frames = []

# Buffer for frames
frame_buffer = deque(maxlen=30)

# Function to check if a frame is recent
def is_frame_recent(frame_index, recent_frames):
    return any(frame_index - i < 20 for i in recent_frames)

frame_index = 0
drop_count = 0

while True:
    ret, frame = cap.read()

    if not ret:
        print("Frame dropped. Retrying...")
        drop_count += 1
        log_missed_frame(frame_index)

        if drop_count > 5:
            cap.release()
            print("Attempting to reconnect to stream...")
            for attempt in range(reconnection_attempts):
                cap = create_video_capture()
                time.sleep(reconnection_delay)

                if cap.isOpened() and cap.read()[0]:
                    print("Reconnected successfully.")
                    drop_count = 0
                    break
            else:
                print("Failed to reconnect after multiple attempts.")
                break
        continue

    drop_count = 0
    log_processed_frame(frame_index)
    frame_buffer.append((frame, frame_index))

    while frame_buffer:
        current_frame, index = frame_buffer.popleft()
        results = model(current_frame)

        for result in results:
            for box in result.boxes:
                if box.conf >= 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    class_id = int(box.cls)
                    class_name = model.names[class_id]

                    width = x2 - x1
                    height = y2 - y1

                    cv2.rectangle(current_frame, (x1, y1), (x2, y2), (0, 255, 255), 1)

                    centroid_x = int((x1 + x2) / 2)
                    centroid_y = int((y1 + y2) / 2)
                    cv2.circle(current_frame, (centroid_x, centroid_y), 5, (255, 255, 0), -1)

                    if width > 5 and height > 5:
                        if cv2.pointPolygonTest(np.array(zone, np.int32), (centroid_x, centroid_y), False) >= 0:
                            if not is_frame_recent(index, recent_frames):
                                recent_frames.append(index)

                                if class_name == 'blue_box':
                                    chain_box_count += 1
                                    cv2.rectangle(current_frame, (x1, y1), (x2, y2), (255, 255, 0), 5)
                                elif class_name == 'brown_box':
                                    rect_box_count += 1
                                    cv2.rectangle(current_frame, (x1, y1), (x2, y2), (255, 0, 255), 5)

        cv2.polylines(current_frame, [np.array(zone, np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)
        cv2.putText(current_frame, f"FRAME_COUNT: {frame_index}", (100, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(current_frame, f"Box Count A: {chain_box_count}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        cv2.putText(current_frame, f"Box Count B: {rect_box_count}", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 250), 3)

        # Save the frame to the output video
        out.write(current_frame)

        # Resize and display the frame
        disp = cv2.resize(current_frame, (800, 800))
        cv2.imshow('Object Detection', disp)

        if cv2.waitKey(1) & 0xFF == ord('s'):
            frame_filename = f"saved_frame_{index}.png"
            cv2.imwrite(frame_filename, current_frame)
            print(f"Frame saved: {frame_filename}")

    frame_index += 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

end_time = time.strftime('%Y-%m-%d %H:%M:%S')
with open(log_file, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([end_time, "Stream Ended", "", ""])
    writer.writerow(["", "Total Frames Processed", frame_index, ""])
    writer.writerow(["", "Total Missed Frames", missed_frame_count, ""])

cap.release()
out.release()
cv2.destroyAllWindows()
