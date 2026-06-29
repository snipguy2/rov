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
        
    def update_stream_status(self, is_connected):
        if is_connected:
            self.stacked_widget.setCurrentWidget(self.imageLabel)
        else:
            self.stacked_widget.setCurrentWidget(self.placeholderLabel)
            
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
        """Updates the video source dynamically."""
        # 1. Stop current capture
        self.worker.stop()
        self.worker.wait()
        
        # 2. Update the URL
        # If localhost/sim, use the standard local port
        if ip_address.strip().lower() in ["localhost", "127.0.0.1", "sim"]:
            self.worker.update_target(ip_address.strip().lower())
        else:
            self.worker.update_target(ip_address.strip().lower())
            
        # 3. Restart the worker with the new URL
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

    def update_target(self, new_ip: str):
        """Thread-safe method called by the main UI thread to change targets."""
        self.target_ip = new_ip

    def run(self):
        while self.ThreadActive:
            # 1. If the IP target changed, release the old resource and reconfigure
            if self.current_ip != self.target_ip or self.cap is None:
                self.current_ip = self.target_ip
                if self.cap is not None:
                    self.cap.release()
                    self.cap = None
                
                # Set FFMPEG options dynamically right before initialization
                if self.current_ip in ["localhost", "127.0.0.1", "sim"]:
                    stream_url = "tcp://localhost:1234"
                    # Localhost uses server mode ('listen') and a short 2-second timeout
                    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|rtsp_flags;listen|timeout;2000000|rw_timeout;2000000'
                else:
                    stream_url = f"tcp://{self.current_ip}:1234"
                    # Remote connections REMOVE 'listen' so we act as a normal network client connection
                    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|timeout;2000000|rw_timeout;2000000'
                
                self.cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

            # 2. Check if the connection stream succeeded
            if not self.cap.isOpened():
                self.ConnectionStatus.emit(False)
                self.cap.release()
                self.cap = None
                
                # Intermittent 5-second sleep that wakes up instantly if the user updates the IP box
                for _ in range(50):
                    if not self.ThreadActive or self.current_ip != self.target_ip:
                        break
                    time.sleep(0.1)
                continue
                
            # 3. Read incoming frames from the network stream
            ret, frame = self.cap.read()
            if not ret:
                self.ConnectionStatus.emit(False)
                self.cap.release()
                self.cap = None
                
                for _ in range(50): 
                    if not self.ThreadActive or self.current_ip != self.target_ip:
                        break
                    time.sleep(0.1)
                continue
            
            # 4. Stream successfully reading frames
            self.ConnectionStatus.emit(True) 
            
            flippedImage = cv2.flip(frame, 1)
            qtFormatted = QImage(flippedImage.data, flippedImage.shape[1], flippedImage.shape[0], QImage.Format.Format_RGB888)
            pic = qtFormatted.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
            self.ImageUpdate.emit(pic)

        # Thread closing cleanup
        if self.cap is not None:
            self.cap.release()

    def stop(self):
        self.ThreadActive = False
        

class SensorMonitorWidget(QWidget):
    """Visual panel that expands dynamically to match any input dataclass schema structure."""
    file_selected = pyqtSignal(str)
    connect_requested = pyqtSignal(str)

    def __init__(self, data_class_type: Any):
        super().__init__()
        self.data_class_type = data_class_type
        
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

        # MAKE SURE THIS EXACT LINE IS HERE (with the 'self.' prefix)
        self.watchdog_timeout_ms = 3000  

        self.watchdog_timer.start(self.watchdog_timeout_ms)

    def trigger_connection(self):
        """Fires when the connect button is clicked."""
        ip_addr = self.ip_input.text().strip()
        if ip_addr:
            self.status_label.setStyleSheet("color: orange;")
            self.status_label.setText(f"Attempting to connect to {ip_addr}...")
            self.connect_requested.emit(ip_addr)

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