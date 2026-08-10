# controllers.py
import csv
import os
import json
import socket
import random
import time
import select
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from models import SensorReadings
from views import SensorMonitorWidget
from dataclasses import asdict
from models import ROVCommand

class NetworkReceiverThread(QThread):
    new_packet = pyqtSignal(SensorReadings) # Emits dataclass
    connection_status = pyqtSignal(str, bool)
    
    def __init__(self, ip_address:str, port:int=5005):
        super().__init__()
        self.port = port
        self.ip = ip_address
        self.socket = None
        self.is_running = False
        self.latest_packet = None # Store the most recent data here
    
    def send_command(self, cmd_json: str):
        """Slot to be called from the main thread to send data via the thread's socket."""
        if self.socket:
            try:
                self.socket.sendall(cmd_json.encode('utf-8'))
            except Exception as e:
                print(f"NetworkReceiverThread send error: {e}")
                
    def send_rov_command(self, command: ROVCommand):
        if self.socket:
            try:
                # Reuse the JSON + newline serialization used in rpi_sender.py
                payload = json.dumps(asdict(command))
                self.socket.sendall((payload + '\n').encode('utf-8'))
            except Exception as e:
                print(f"Failed to send command: {e}")
    
    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.5) 
        self.is_running = True
        
        try:
            self.socket.connect((self.ip, self.port))
            print("DEBUG: Connection success. Sleeping 1s to allow UI to sync.")
            
            # --- CRITICAL: Ignore incoming data for 1 second ---
            start_time = time.time()
            while time.time() - start_time < 1.0:
                # Keep the thread alive but do NOT process incoming packets
                time.sleep(0.1)
                
            # --- Now begin the loop ---
            while self.is_running:
                ready, _, _ = select.select([self.socket], [], [], 0.5)
                if ready:
                    data = self.socket.recv(4096)
                    if not data: break
                    
                    # Process lines safely
                    lines = data.decode('utf-8').splitlines()
                    for line in lines:
                        if line:
                            data_dict = json.loads(line)
                            self.latest_packet = SensorReadings(**data_dict)
                
                # CRITICAL: Yield CPU to the GUI thread
                self.msleep(10) 
                
        except Exception as e:
            print(f"DEBUG: Socket error: {e}")
        finally:
            self.socket.close()
            
    def stop(self):
        self.is_running = False
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except Exception:
                pass
        self.wait(1000) # Give it time to close


class TelemetryController:
    def __init__(self, view):
        self.view = view
        self.network_thread = None
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.generate_simulated_data)

    def handle_connection_request(self, ip_address):
        # 1. Stop any existing processes
        self.stop_all()

        # 2. Router: Simulation vs Network
        if ip_address in ["sim", "127.0.0.1", "localhost"]:
            print("DEBUG: Entering SIMULATION mode.")
            self.sim_timer.start(1000) # 10Hz simulation
        else:
            print(f"DEBUG: Connecting to real hardware at {ip_address}")
            self.network_thread = NetworkReceiverThread(ip_address)
            # Link thread to view without complex signals
            self.network_thread.start()
            # Start your existing polling timer for network data
            self.view.poll_timer.start(100)
            
    def send_thruster_command(self, thruster_ints: list[int]):
        """Receives the 0-255 integer list from ROVControlPanel and sends to RPi."""
        command_packet = ROVCommand(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            thruster_values=thruster_ints # Now containing integers 0-255
        )
        
        if self.network_thread and self.network_thread.isRunning():
            self.network_thread.send_rov_command(command_packet)
        else:
            # Fallback or debug print when testing in simulation mode
            # print(f"DEBUG (Simulated Serial Out): {thruster_ints}")
            pass

    def generate_simulated_data(self):
        """Creates dummy data and sends it to the View exactly like a real packet."""
        data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "temperature": random.uniform(20.0, 30.0),
            "humidity": random.uniform(40.0, 60.0),
            "pressure": random.uniform(1000.0, 1010.0),
            "voltage": random.uniform(3.7, 4.2),
            "air_quality": random.uniform(15.0, 30.0)
        }
        # Direct injection: The view doesn't know it's fake!
        self.view.update_display(SensorReadings(**data))

    def stop_all(self):
        self.sim_timer.stop()
        if self.network_thread:
            self.network_thread.is_running = False
            self.network_thread.wait()
            