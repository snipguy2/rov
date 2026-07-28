# views.py
import os
from typing import Any
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QVBoxLayout, QPushButton, QFileDialog,
    QHBoxLayout, QLineEdit
)

from dataclasses import fields
from PyQt6.QtGui import QImage, QPixmap

import cv2, time
    
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|rtsp_flags;listen'
STREAM_URL = 'tcp://localhost:1234' 

# views.py
import os
from typing import Any
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
# Added QStackedWidget to the imports below
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QPushButton, QFileDialog, QStackedWidget
from dataclasses import fields
from PyQt6.QtGui import QImage, QPixmap

import cv2, time
    
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|rtsp_flags;listen'
STREAM_URL = 'tcp://localhost:1234' 

class StreamWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.create_widgets()
        self.apply_layout()
        
        # Instantiate a SINGLE persistent worker thread
        self.worker = Worker('localhost')
        self.worker.ImageUpdate.connect(self.image_update)
        self.worker.ConnectionStatus.connect(self.update_stream_status)
        # --- Avoiding starting stream up on init with sim data ---"
        # self.worker.start()
        
    def image_update(self, image):
        self.imageLabel.setPixmap(QPixmap.fromImage(image))
        
    def update_stream_status(self, status: bool):
        if status:
            self.stacked_widget.setCurrentWidget(self.imageLabel)
            self.placeholderLabel.setStyleSheet("background-color: #222; color: #2ecc71; font-size: 16px; border: 1px solid #2ecc71;")
            self.placeholderLabel.setText("Stream Connected")
        else:
            self.stacked_widget.setCurrentWidget(self.placeholderLabel)
            # Yellow for connecting/retry
            self.placeholderLabel.setStyleSheet("background-color: #222; color: #f1c40f; font-size: 16px; border: 1px solid #f1c40f;")
            self.placeholderLabel.setText("Connecting to Stream...")
            
    def create_widgets(self):
        self.stacked_widget = QStackedWidget()
        
        self.placeholderLabel = QLabel("Video Stream Unavailable (Retrying...)")
        self.placeholderLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholderLabel.setStyleSheet("background-color: #222; color: #fff; font-size: 16px; border: 1px solid red;")
        
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.stacked_widget.addWidget(self.placeholderLabel)
        self.stacked_widget.addWidget(self.imageLabel)
        
    def apply_layout(self):
        self.layout.addWidget(self.stacked_widget)
        self.setLayout(self.layout)

    def set_stream_ip(self, ip_address: str):
        # 1. Stop the thread cleanly
        self.worker.ThreadActive = False
        self.worker.wait()
        
        # 2. Update target and restart
        self.worker.target_ip = ip_address.strip()
        self.worker.ThreadActive = True
        self.worker.start()


class Worker(QThread):
    ImageUpdate = pyqtSignal(QImage)
    ConnectionStatus = pyqtSignal(bool)

    def __init__(self, initial_ip: str):
        super().__init__()
        self.current_ip = initial_ip
        self.target_ip = initial_ip
        self.ThreadActive = True
        self.cap = None
    
    
    def run(self):
        while self.ThreadActive:
            # Check if we are doing local stream or RTSP
            if self.target_ip in ["localhost", "127.0.0.1"]:
                # The script uses TCP mpegts
                stream_url = "tcp://localhost:8554"
            else:
                # The RPi uses RTSP
                stream_url = f"rtsp://{self.target_ip}:8554/cam"
            
            # 3. Initialize capture
            self.cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

            if not self.cap.isOpened():
                self.ConnectionStatus.emit(False)
                time.sleep(2)
                continue

            while self.ThreadActive:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                self.ConnectionStatus.emit(True)
                
                # Convert BGR to RGB for PyQt
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                qt_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
                self.ImageUpdate.emit(qt_img.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio))

            self.cap.release()

    def update_target(self, new_ip: str):
        """Thread-safe method called by the main UI thread to change targets."""
        self.target_ip = new_ip


class SensorMonitorWidget(QWidget):
    """Visual panel that expands dynamically to match any input dataclass schema structure."""
    file_selected = pyqtSignal(str)
    connect_requested = pyqtSignal(str)

    def __init__(self, data_class_type, controller=None): # Add controller parameter
        super().__init__()
        self.controller = controller
        self.data_class_type = data_class_type
        self.controller = controller # Initialize as None, then set in main.py
        
        self.setWindowTitle("Dynamic Sensor Telemetry")
        # Let the window resize automatically based on contents
        self.setSizePolicy(self.sizePolicy().Policy.Minimum, self.sizePolicy().Policy.Minimum)
        
        # Track layout reference targets dynamically
        self.value_labels = {}

        main_layout = QVBoxLayout(self)
        grid_layout = QGridLayout()
        main_layout.addLayout(grid_layout)

        # --- NEW: Network Connection UI ---
        network_layout = QHBoxLayout()
        self.ip_input = QLineEdit("192.168.110.100") # Default placeholder IP
        self.ip_input.setPlaceholderText("Enter RPi IP Address...")
        self.connect_btn = QPushButton("Connect to Pi")
        self.connect_btn.clicked.connect(self.trigger_connection)
        network_layout.addWidget(QLabel("<b>RPi IP:</b>"))
        network_layout.addWidget(self.ip_input)
        network_layout.addWidget(self.connect_btn)
        main_layout.addLayout(network_layout)
        # ----------------------------------

        # 1. Dynamically read properties and construct visual interface blocks
        for i, field in enumerate(fields(self.data_class_type)):
            field_title = field.name.replace('_', ' ').capitalize()
            
            name_label = QLabel(f"<b>{field_title}:</b>")
            val_label = QLabel("Waiting...")
            val_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            grid_layout.addWidget(name_label, i, 0)
            grid_layout.addWidget(val_label, i, 1)

            # Map the field name string directly to its label object reference
            self.value_labels[field.name] = val_label

        # Controls for logging files
        self.log_button = QPushButton("Select Log File Destination...")
        self.log_button.clicked.connect(self.prompt_for_file)
        main_layout.addWidget(self.log_button)

        self.log_status_label = QLabel("Logging Status: Disabled (No file chosen)")
        self.log_status_label.setWordWrap(True)
        main_layout.addWidget(self.log_status_label)

        self.status_label = QLabel("Connecting to telemetry stream...")
        main_layout.addWidget(self.status_label)

        # --- Watchdog Timer Setup ---
        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.setSingleShot(True)  # Only trigger once when time runs out
        self.watchdog_timer.timeout.connect(self.handle_stream_timeout)

        self.watchdog_timeout_ms = 3000  

        self.watchdog_timer.start(self.watchdog_timeout_ms)
        
        #timer for reading data from network
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.check_for_data)
        self.poll_timer.start(100) # Poll at 10Hz

    def check_for_data(self):
        if self.controller and self.controller.network_thread:
            # Check if the thread has new data
            if self.controller.network_thread.latest_packet:
                # Capture the current packet
                packet = self.controller.network_thread.latest_packet
                
                # Clear it IMMEDIATELY so the next poll doesn't see it
                self.controller.network_thread.latest_packet = None
                
                # Now update the display
                self.update_display(packet)

    def emit_connection_request(self):
        # 2. Get the IP from the text box
        ip = self.ip_input.text() 
        print(f"DEBUG: Triggering connect_requested for: {ip}")
        # 3. Emit
        self.connect_requested.emit(ip)

    def trigger_connection(self):
        ip = self.ip_input.text() # Get the IP from your QLineEdit
        print(f"DEBUG: Button clicked! Emitting signal with IP: {ip}")
        self.connect_requested.emit(ip) # THIS IS THE CRITICAL LINE

    def prompt_for_file(self):
        """Opens a file dialog system frame to save incoming data streams."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Log File Destination",
            "",
            "CSV Files (*.csv);;Text Files (*.txt)"
        )
        if file_path:
            self.file_selected.emit(file_path)

    def update_display(self, data: Any):
        print(f"updating display....")
        """Loops dynamically through the payload attributes to push text to fields."""

        # Keep the global watchdog alive as long as we are receiving packets at all
        self.watchdog_timer.start(self.watchdog_timeout_ms)

        for field in fields(data):
            val = getattr(data, field.name)
            
            if field.name in self.value_labels:
                label = self.value_labels[field.name]

                # Check if the individual sensor failed to report data
                if val is None:
                    # Prevent appending "Stale" infinitely if it's already stale
                    if "Stale" not in label.text() and label.text() != "Waiting...":
                        label.setStyleSheet("color: gray;")
                        label.setText(f"Stale ({label.text()})")
                    elif label.text() == "Waiting...":
                        label.setStyleSheet("color: gray;")
                        label.setText("Stale (No Data)")
                else:
                    # Sensor is reporting valid data, format normally and remove stale styling
                    display_text = f"{val:.2f}" if isinstance(val, float) else str(val)
                    label.setStyleSheet("") 
                    label.setText(display_text)
                
        self.status_label.setStyleSheet("color: green;")
        self.status_label.setText("🟢 Metrics parsed from incoming dataclass container")

    # --- Failure state handler ---
    def handle_stream_timeout(self):
        """Triggers when the watchdog timer expires due to dropped packets."""
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_label.setText("🔴 FAILING: Telemetry stream connection lost!")
        
        # Visually indicate that the currently displayed numbers are no longer live
        for label in self.value_labels.values():
            if label.text() != "Waiting...":
                label.setStyleSheet("color: gray;")
                label.setText(f"Stale ({label.text()})")

    def update_logging_status(self, path: str):
        """Updates the visual labeling to display where active file streaming is printing."""
        file_name = os.path.basename(path)
        self.log_status_label.setText(f"📝 <b>Active Log:</b> {file_name}")
        self.log_button.setText("Change Log File...")