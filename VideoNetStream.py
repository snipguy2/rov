import cv2
import os

# Force FFmpeg to use TCP for RTSP streams
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|rtsp_flags;listen'

# Replace with your actual stream URL
# Example: 'rtsp://user:pass@192.168.1.100:554/live'
url = 'tcp://localhost:1234' 

cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow('TCP Network Stream', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
