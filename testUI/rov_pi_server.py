# rov_pi_server.py
# on-board code that runs indefinitely on rov sbc

import socket
import json
import time
import random
import selectors
import serial

# --- PySerial Setup for Arduino ---
# Replace '/dev/ttyUSB0' with your actual Arduino port (e.g., 'COM3' on Windows)
try:
    arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    print("Arduino connected successfully via PySerial.")
except Exception as e:
    print(f"Warning: Could not connect to Arduino: {e}. Running in dummy mode.")
    arduino = None

sel = selectors.DefaultSelector()

def accept_wrapper(server_sock):
    client_sock, addr = server_sock.accept()
    print(f"Accepted connection from {addr}")
    client_sock.setblocking(False)
    
    # Register client socket for reading (incoming commands from PC)
    data = selectors.DataType(addr=addr, inb=b"")
    sel.register(client_sock, selectors.EVENT_READ, data=data)

def service_connection(key, mask):
    client_sock = key.fileobj
    addr = key.data.addr
    
    if mask & selectors.EVENT_READ:
        incoming_data = client_sock.recv(1024)
        if incoming_data:
            # Process lines (handling potential batching via newline delimiter)
            for line in incoming_data.decode('utf-8').splitlines():
                if line.strip():
                    try:
                        parsed_cmd = json.loads(line)
                        # Extract the 0-255 integer list
                        thruster_vals = parsed_cmd.get("thruster_values", [])
                        
                        if thruster_vals:
                            # Format as comma-separated string for Arduino: e.g., "127,255,127,..."
                            payload_bytes = ",".join(map(str, thruster_vals)) + '\n'
                            
                            if arduino and arduino.is_open:
                                arduino.write(payload_bytes.encode('utf-8'))
                                print(f"Sent to Arduino: {payload_bytes.strip()}")
                            else:
                                print(f"Simulated Arduino Out: {payload_bytes.strip()}")
                                
                    except json.JSONDecodeError:
                        print(f"Malformed JSON received from {addr}")
        else:
            print(f"Closing connection to {addr}")
            sel.unregister(client_sock)
            client_sock.close()

def start_pi_server(host='0.0.0.0', port=5005):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    server_socket.setblocking(False)
    sel.register(server_socket, selectors.EVENT_READ, data=None)
    
    print(f"Bidirectional ROV Server running on {host}:{port}...")
    
    last_telemetry_time = time.time()
    
    try:
        while True:
            events = sel.select(timeout=0.05)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
            
            # Periodically push telemetry out to connected clients (10Hz)
            if time.time() - last_telemetry_time >= 0.1:
                last_telemetry_time = time.time()
                
                sensor_data = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "temperature": random.uniform(18.0, 35.0),
                    "humidity": random.uniform(30.0, 75.0),
                    "pressure": random.uniform(980.0, 1030.0),
                    "voltage": random.uniform(3.1, 5.0),
                    "air_quality": random.uniform(10.0, 50.0) 
                }
                payload = (json.dumps(sensor_data) + "\n").encode('utf-8')
                
                # Broadcast or send to registered client sockets
                for key in list(sel.get_map().values()):
                    sock = key.fileobj
                    if sock != server_socket and key.data is not None:
                        try:
                            sock.sendall(payload)
                        except Exception:
                            # Handle disconnected sockets cleanly
                            sel.unregister(sock)
                            sock.close()
                            
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        sel.close()
        if arduino and arduino.is_open:
            arduino.close()

if __name__ == "__main__":
    start_pi_server()