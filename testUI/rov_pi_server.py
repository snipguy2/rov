import socket
import json
import time
import random
from dataclasses import asdict

# Assuming your SensorReadings class exists here too or you define a dict
def start_pi_publisher(host='0.0.0.0', port=5005):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(1)
    
    print(f"Waiting for telemetry subscriber...")
    client_sock, addr = server_socket.accept()
    print(f"Subscriber connected: {addr}")
    
    try:
        while True:
            # 1. Capture/Simulate sensor data
            data = {
                "timestamp": time.strftime("%H:%M:%S"),
                "temperature" : random.uniform(18.0, 35.0),
                "humidity" : random.uniform(30.0, 75.0),
                "pressure" : random.uniform(980.0, 1030.0),
                "voltage" : random.uniform(3.1, 5.0),
                "air_quality" : random.uniform(10.0, 50.0) 
            }
            # 2. Publish
            client_sock.sendall((json.dumps(data) + "\n").encode('utf-8'))
            time.sleep(0.1) # 10Hz update rate
            
    except Exception as e:
        print(f"Connection lost: {e}")
    finally:
        client_sock.close()
        
def main():
    start_pi_publisher()


if __name__ == "__main__":
    main()