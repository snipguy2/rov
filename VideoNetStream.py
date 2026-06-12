import cv2
import os

# Force FFmpeg to use TCP for RTSP streams
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|rtsp_flags;listen'

# Replace with your actual stream URL
# Example: 'rtsp://user:pass@192.168.1.100:554/live'
VID_URL = 'tcp://localhost:1234' 

def connect_to_stream(url:str) -> None:
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("Error: Could not open video stream.")
    return cap

def execute(capture: cv2.VideoCapture):
    while True:
        ret, frame = capture.read()
        if not ret:
            break

        cv2.imshow('TCP Network Stream', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    
def main():
    cap: cv2.VideoCapture = connect_to_stream(VID_URL)
    
    # Run loop for video refresh:
    execute(cap)
    #===========================
    
    # Deallocate and release cv2 capture stream:
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()


