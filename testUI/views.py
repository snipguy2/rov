# views.py
import os
from typing import Any
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QPushButton, QFileDialog
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
        self.worker = Worker()
        self.worker.ImageUpdate.connect(self.image_update)
        self.worker.start()
        
    def image_update(self, image):
        self.imageLabel.setPixmap(QPixmap.fromImage(image))
        
    def create_widgets(self):
        self.imageLabel = QLabel()
        self.cancelButton = QPushButton("Cancel")
        
    def setup_signals(self):
        self.cancelButton.clicked.connect(self.stop_video_feed)
        
    def apply_layout(self):
        self.layout.addWidget(self.imageLabel)
        self.setLayout(self.layout)
        
    def stop_video_feed(self):
        self.worker.stop()
        
class Worker(QThread):
    ImageUpdate = pyqtSignal(QImage)
    def run(self):
        self.ThreadActive = True
        self.cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
        while self.ThreadActive:
            if not self.cap.isOpened():
                print("Error: Could not open video stream.")
                self.cap.release()
                time.sleep(3)
                self.cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
                continue
            ret, frame = self.cap.read()
            if not ret:
                break
            
            #self.image = cv2.cvtColor(frame, cv2.COLOR_BayerGB2RGB)
            self.image = frame
            flippedImage = cv2.flip(self.image, 1)
            qtFormatted = QImage(flippedImage.data, flippedImage.shape[1], flippedImage.shape[0], QImage.Format.Format_RGB888)
            pic = qtFormatted.scaled(640,480, Qt.AspectRatioMode.KeepAspectRatio)
            self.ImageUpdate.emit(pic)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def stop(self):
        self.ThreadActive = False
        self.cap.release()
        cv2.destroyAllWindows()

class SensorMonitorWidget(QWidget):
    """Visual panel that expands dynamically to match any input dataclass schema structure."""
    file_selected = pyqtSignal(str)

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

        self.watchdog_timer.start(self.watchdog_timeout_ms)

        for field in fields(data):
            val = getattr(data, field.name)
            display_text = f"{val:.2f}" if isinstance(val, float) else str(val)
            
            # Match the variable name to our stored label and change its text
            if field.name in self.value_labels:
                # Optionally remove "Stale" styling if the stream recovers
                self.value_labels[field.name].setStyleSheet("") 
                self.value_labels[field.name].setText(display_text)
                
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