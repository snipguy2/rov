# controllers.py
import csv
import os
import json
import socket
import random
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from models import SensorReadings
from views import SensorMonitorWidget

class NetworkReceiverThread(QThread):
    """Background thread to handle blocking TCP socket connections."""
    new_packet = pyqtSignal(SensorReadings)
    connection_status = pyqtSignal(str, bool) 

    def __init__(self, ip: str, port: int = 5005):
        super().__init__()
        self.ip = ip
        self.port = port
        self.is_running = True
        self.socket = None

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(3.0) 
        
        try:
            self.socket.connect((self.ip, self.port))
            self.connection_status.emit(f"🟢 Connected to {self.ip}:{self.port}", True)
            
            # Change from None (infinite block) to 1.0 second.
            # This forces f.readline() to throw a timeout every 1 sec if there's no data,
            # allowing the while loop to check if self.is_running has changed to False.
            self.socket.settimeout(1.0) 
            
            with self.socket.makefile('r', encoding='utf-8') as f:
                while self.is_running:
                    try:
                        line = f.readline()
                        if not line:
                            break 
                        
                        data_dict = json.loads(line)
                        packet = SensorReadings(**data_dict)
                        self.new_packet.emit(packet)
                    except socket.timeout:
                        # Just a read timeout, loop around and check if we are still running
                        continue
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            if self.is_running: # Only trigger fallback if the connection genuinely died
                self.connection_status.emit("Pi Unavailable", False)
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except Exception:
                    pass
            if self.is_running:
                self.connection_status.emit("Disconnected", False)

    def stop(self):
        self.is_running = False
        
        # CRITICAL FIX: Forcefully snap the socket out of any hanging operation
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except Exception:
                pass
                
        # Wait a maximum of 500ms before abandoning the thread to avoid UI freeze
        self.wait(500)


class TelemetryController:
    """Manages routing of data, with a switch to activate simulation upon request."""
    def __init__(self, view: SensorMonitorWidget):
        self.view = view
        self.log_file_path = None
        
        # Setup Simulation Timer (initially stopped)
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.generate_simulated_data)
        
        # Connect to UI signals
        self.view.file_selected.connect(self.set_active_log_file)
        # Assuming your UI has a signal for connection requests
        self.view.connect_requested.connect(self.handle_connection_request)

    def handle_connection_request(self, ip_address: str):
        """Switches mode based on the user's input."""
        ip_clean = ip_address.strip().lower()
        
        # Stop any existing simulation
        self.sim_timer.stop()
        
        if ip_clean in ['localhost', '127.0.0.1', 'sim']:
            self.view.status_label.setText(f"Status: Simulating ({ip_clean})")
            self.sim_timer.start(1000)
        else:
            self.view.status_label.setText(f"Status: Connecting to {ip_address}...")
            # Here you would trigger your actual network thread connection
            # self.start_network_connection(ip_address)

    def set_active_log_file(self, path: str):
        self.log_file_path = path
        self.view.update_logging_status(path)
        
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            with open(path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                dummy = SensorReadings("", 0, 0, 0, 0, 0)
                writer.writerow(dummy.csv_header)

    def generate_simulated_data(self):
        """Generates fallback local data if localhost/sim mode is active."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_packet = SensorReadings(
            timestamp=current_time,
            temperature=random.uniform(18.0, 35.0),
            humidity=random.uniform(30.0, 75.0),
            pressure=random.uniform(980.0, 1030.0),
            voltage=random.uniform(3.1, 5.0),
            air_quality=random.uniform(10.0, 50.0)
        )
        
        self.view.update_display(new_packet)

        if self.log_file_path:
            try:
                with open(self.log_file_path, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(new_packet.csv_row)
            except IOError as e:
                print(f"Error appending data: {e}")