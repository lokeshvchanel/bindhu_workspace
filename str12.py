import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# Initialize YOLO model
model = YOLO('blue_brown_box.pt')

# Twilio credentials (replace with your actual credentials)
ACCOUNT_SID = "ACb9195ee49a5fddf63130178973ed4185"
AUTH_TOKEN = "e7a2f7812787a31f231f6016259588da"
FROM_WHATSAPP_NUMBER = 'whatsapp:+14155238886'
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Email credentials (replace with your actual credentials)
EMAIL_ADDRESS = "prophetnithya@gmail.com"
EMAIL_PASSWORD = "mkbx oqnz igzd gfxo"

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'detection_started' not in st.session_state:
    st.session_state.detection_started = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'config_done' not in st.session_state:
    st.session_state.config_done = False
if 'config_username' not in st.session_state:
    st.session_state.config_username = ""
if 'config_password' not in st.session_state:
    st.session_state.config_password = ""
if 'config_link' not in st.session_state:
    st.session_state.config_link = ""
if 'object_count' not in st.session_state:
    st.session_state.object_count = 0

# User credentials
users = {
    "admin": "admin123",
    "user1": "password1",
    "user2": "password2"
}

# Function to check credentials
def authenticate(username, password):
    return username in users and users[username] == password

# Function to send WhatsApp message
def send_whatsapp_message(count, phone_number):
    try:
        message = client.messages.create(
            body=f'Detection completed. Total objects detected: {count}',
            from_=FROM_WHATSAPP_NUMBER,
            to=f'whatsapp:{phone_number}'
        )
        st.success(f"WhatsApp message sent to {phone_number} with {count} objects detected.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Function to send email notifications
def send_email_notifications(count, recipient_emails):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ", ".join(recipient_emails)
        msg['Subject'] = "Detection Report"
        body = f"Detection completed. Total objects detected: {count}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipient_emails, msg.as_string())

        st.success(f"Email sent to {len(recipient_emails)} recipients successfully!")
    except Exception as e:
        st.error(f"Failed to send email. Error: {e}")
    finally:
        server.quit()

# Function to display login page
def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.page = 'config'
        else:
            st.error("Invalid credentials! Please try again.")

# Function to display config page
def config_page():
    st.title("Config Page")
    st.write("Please fill in the configuration details.")

    st.session_state.config_username = st.text_input("Config Username", st.session_state.config_username)
    st.session_state.config_password = st.text_input("Config Password", type="password", value=st.session_state.config_password)
    st.session_state.config_link = st.text_input("Config Link", st.session_state.config_link)

    if st.button("Save Config"):
        st.success("Configuration saved!")
        st.session_state.config_done = True
        st.session_state.page = 'detection'

# Function to start or stop detection
def manage_detection():
    if st.session_state.detection_started:
        st.header("Detection Page")
        st.write("Detection in progress...")
        if st.button("Stop Detection"):
            st.session_state.detection_started = False
            st.success("Detection stopped.")
            st.session_state.page = 'communication'
    else:
        st.header("Detection Page")
        st.write("Ready to start detection.")
        if st.button("Start Detection"):
            st.session_state.detection_started = True
            st.success("Detection started!")

# Function to perform detection
def perform_detection():
    st.header("Detection Page")
    # HTTP stream or video file input section
    input_type = st.radio("Choose input type:", ("HTTP Stream", "Video File"))

    http_stream = None
    uploaded_file = None

    if input_type == "HTTP Stream":
        # User inputs the HTTP stream URL
        http_stream = st.text_input("Enter HTTP stream link (e.g.,  http://192.168.0.100:8080/video)")
    else:
        uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

    # Phone number input (Static phone number)
    phone_number = '+919442493256'

    # Email addresses input (Allow up to 10)
    email_addresses = st.text_area("Enter up to 10 email addresses separated by commas")

    # Convert entered email addresses into a list
    recipient_emails = [email.strip() for email in email_addresses.split(',') if email.strip()]

    # Ensure the user inputs up to 10 valid email addresses
    if len(recipient_emails) > 10:
        st.error("You can only enter up to 10 email addresses.")

    if st.button("Stop Detection"):
        st.session_state.detection_started = False
        send_whatsapp_message(st.session_state.object_count, phone_number)
        if recipient_emails:
            send_email_notifications(st.session_state.object_count, recipient_emails)
        st.success(f"Detection stopped. Total objects detected: {st.session_state.object_count}")
        st.session_state.page= "communication"
    if (http_stream or uploaded_file) and phone_number:
        if st.button("Start Detection"):
            st.session_state.object_count = 0
            st.session_state.detection_started = True

            if http_stream:
                cap = cv2.VideoCapture(http_stream,cv2.CAP_FFMPEG)#,cv2.CAP_FFMPEG
            elif uploaded_file:
                temp_video_path = "temp_uploaded_video.mp4"
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded_file.read())
                cap = cv2.VideoCapture(temp_video_path)

            if not cap.isOpened():
                st.error("Error: Unable to access the video stream. Check the input and try again.")
            else:
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                print("width ----->",width)
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print("height ----->",height)

                folder_path = 'output_videos'
                os.makedirs(folder_path, exist_ok=True)
                output_path = os.path.join(folder_path, 'output_detection.mp4')
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                zone_width = 50
                zone_height = 10
                center_x = width // 2
                center_y = height // 2
                zone = [
                    (center_x - zone_width // 2, zone_height),
                    (center_x + zone_width // 2, zone_height),
                    (center_x + zone_width // 2, height - zone_height),
                    (center_x - zone_width // 2, height - zone_height)
                ]

                progress_bar = st.progress(0)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0 else None
                current_frame = 0
                recent_frames = []

                def is_frame_recent(frame_index, recent_frames):
                    for i in recent_frames:
                        if frame_index - i < 30:
                            return True
                    return False

                frame_index = 0
                while cap.isOpened() and st.session_state.detection_started:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    results = model(frame)

                    # Draw the detection zone
                    cv2.polylines(frame, [np.array(zone, np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)

                    for result in results:
                        for box in result.boxes:
                            # Filter by confidence
                            if box.conf >= 0.60:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                bbox_width = x2 - x1
                                bbox_height = y2 - y1

                                # Draw the bounding box
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

                                # Calculate and draw the centroid
                                centroid_x = int((x1 + x2) / 2)
                                centroid_y = int((y1 + y2) / 2)
                                cv2.circle(frame, (centroid_x, centroid_y), 5, (255, 255, 0), -1)
                                size_text = f"W: {bbox_width} H: {bbox_height}"
                                cv2.putText(frame, size_text, (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                                # Check if the centroid is within the zone
                                if bbox_width > 50 and bbox_height > 50:
                                    if cv2.pointPolygonTest(np.array(zone, np.int32), (centroid_x, centroid_y), False) >= 0:
                                        if not is_frame_recent(frame_index, recent_frames):
                                            if bbox_height > 75:
                                                st.session_state.object_count += 2  # Large object count as 2
                                            else:
                                                st.session_state.object_count += 1  # Normal object count as 1

                                            recent_frames.append(frame_index)
                                            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 5)

                    # cv2.putText(frame, f"Count: {st.session_state.object_count}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5)

                    out.write(frame)
                    if frame_count:
                        progress_bar.progress(int((current_frame / frame_count) * 100))
                    current_frame += 1
                    frame_index += 1

                cap.release()
                out.release()
                cv2.destroyAllWindows()
                st.session_state.detection_started = False
                send_whatsapp_message(st.session_state.object_count, phone_number)
                if recipient_emails:
                    send_email_notifications(st.session_state.object_count, recipient_emails)
                st.success(f"Detection stopped. Total objects detected: {st.session_state.object_count}")
                # st.session_state.page= "communication"
                progress_bar.empty()
                st.session_state.page = 'communication'
                st.session_state.detection_started = False
                st.session_state.object_count = 0
                # if st.button("Logout"):
                #     st.session_state.logged_in = False
                #     login_page("Login")

# Function to display communication page
def communication_page():
    st.title("Communication Page")
    st.write("Communicating results...")
    if st.button("End Logout"):
        st.session_state.page = 'login'
        st.session_state.logged_in = False
        st.session_state.authenticated = False
        st.session_state.config_done = False
        st.session_state.detection_started = False
        st.session_state.username = ""
        st.session_state.config_username = ""
        st.session_state.config_password = ""
        st.session_state.config_link = ""
        st.session_state.object_count = 0

# Main function to handle page navigation
def main():
    if st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'config':
        # if st.session_state.authenticated:
            config_page()
        # else:
        #     st.warning("Please log in to access the configuration page.")
    elif st.session_state.page == 'detection':
        # if st.session_state.config_done:
            perform_detection()
        # else:
        #     st.warning("Please complete the configuration before starting detection.")
    elif st.session_state.page == 'communication':
        communication_page()
    else:
        st.error("Page not found.")

if __name__ == "__main__":
    main()