# rpi_sender.py
import socket
import json
import time
import random
import selectors
from datetime import datetime
from models import SensorReadings

# Configuration
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 5005       # Telemetry/Command port

sel = selectors.DefaultSelector()

def get_reading(min_val, max_val):
    """10% chance to simulate a dropped sensor (None), otherwise returns a float."""
    return random.uniform(min_val, max_val) if random.random() > 0.10 else None

def accept_wrapper(server_sock):
    conn, addr = server_sock.accept()
    print(f"Connected by PC Client: {addr}!")
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, data=addr)

def service_connection(key, mask):
    conn = key.fileobj
    addr = key.data
    
    if mask & selectors.EVENT_READ:
        try:
            data = conn.recv(1024)
            if data:
                # Process incoming lines from the PC GUI (ROVCommand packets)
                for line in data.decode('utf-8').splitlines():
                    if line.strip():
                        parsed = json.loads(line)
                        thruster_vals = parsed.get("thruster_values", [])
                        if thruster_vals:
                            # Simulate the serial transmission string bound for the Arduino
                            serial_string = ",".join(map(str, thruster_vals))
                            print(f"-> [Simulated Serial to Arduino]: {serial_string}")
            else:
                print(f"Client {addr} disconnected. Unregistering...")
                sel.unregister(conn)
                conn.close()
        except Exception as e:
            print(f"Error handling data from {addr}: {e}")
            sel.unregister(conn)
            conn.close()

def start_server():
    print(f"Starting Bidirectional Telemetry & Command Server on {HOST}:{PORT}...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        server_socket.setblocking(False)
        sel.register(server_socket, selectors.EVENT_READ, data=None)
        
        last_telemetry_time = time.time()
        
        try:
            while True:
                events = sel.select(timeout=0.05)
                for key, mask in events:
                    if key.data is None:
                        accept_wrapper(key.fileobj)
                    else:
                        service_connection(key, mask)
                
                # Push telemetry out at 1Hz (matching your original broadcast rate)
                if time.time() - last_telemetry_time >= 1.0:
                    last_telemetry_time = time.time()
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    packet = SensorReadings(
                        timestamp=current_time, 
                        temperature=get_reading(18.0, 35.0),
                        humidity=get_reading(30.0, 75.0),
                        pressure=get_reading(980.0, 1030.0),
                        voltage=get_reading(3.1, 5.0),
                        air_quality=get_reading(10.0, 50.0)
                    )
                    
                    json_payload = json.dumps(asdict(packet)) + '\n'
                    payload_bytes = json_payload.encode('utf-8')
                    
                    # Send telemetry to all connected client sockets
                    for key in list(sel.get_map().values()):
                        sock = key.fileobj
                        if sock != server_socket and key.data is not None:
                            try:
                                sock.sendall(payload_bytes)
                            except (ConnectionResetError, BrokenPipeError):
                                print("Client connection lost during telemetry broadcast.")
                                sel.unregister(sock)
                                sock.close()
                                
        except KeyboardInterrupt:
            print("\nServer shutting down.")
        finally:
            sel.close()

if __name__ == "__main__":
    start_server()