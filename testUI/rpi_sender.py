# rpi_sender.py
# Simulation logic for feaux RPi 5

import socket
import json
import time
import random
from dataclasses import asdict
from datetime import datetime
from models import SensorReadings

# Configuration
HOST = '0.0.0.0'  # Listen on all available Ethernet/Wi-Fi interfaces
PORT = 5005       # Arbitrary non-privileged port

def get_reading(min_val, max_val):
    """10% chance to simulate a dropped sensor (None), otherwise returns a float."""
    return random.uniform(min_val, max_val) if random.random() > 0.10 else None

def start_server():
    print(f"Starting Telemetry Server on {HOST}:{PORT}...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Allow immediate port reuse after script restart
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        
        while True:
            print("Waiting for PC Client to connect...")
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}!")
            
            with conn:
                try:
                    while True:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Generate payload
                        packet = SensorReadings(
                            timestamp=current_time, 
                            temperature=get_reading(18.0, 35.0),
                            humidity=get_reading(30.0, 75.0),
                            pressure=get_reading(980.0, 1030.0),
                            voltage=get_reading(3.1, 5.0),
                            air_quality=get_reading(10.0, 50.0)
                        )
                        
                        # Serialize dataclass to dictionary, then to JSON string
                        json_payload = json.dumps(asdict(packet))
                        
                        # Send over Ethernet (newline '\n' acts as our packet delimiter)
                        conn.sendall((json_payload + '\n').encode('utf-8'))
                        
                        # Broadcast rate: 1Hz
                        time.sleep(1)
                        
                except (ConnectionResetError, BrokenPipeError):
                    print(f"Client {addr} disconnected. Resetting...")

if __name__ == "__main__":
    start_server()