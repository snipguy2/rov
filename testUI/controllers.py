# controllers.py
import csv
import os
import random
from PyQt6.QtCore import QTimer
from models import SensorReadings
from views import SensorMonitorWidget

class TelemetryController:
    """Manages sampling intervals and automatically mirrors the shape of the data model."""
    def __init__(self, view: SensorMonitorWidget):
        self.view = view
        self.log_file_path = None
        
        self.view.file_selected.connect(self.set_active_log_file)

        # Configure continuous 1-second background polling cycle
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_and_pass_data)
        self.timer.start(1000)

    def set_active_log_file(self, path: str):
        """Prepares destination file pathways by appending column header identifiers."""
        self.log_file_path = path
        self.view.update_logging_status(path)

        # Generate headers dynamically from the model definition if the file is new
        if not os.path.exists(path) or os.stat(path).st_size == 0:
            with open(path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Instantiate a temporary object to grab dynamic headers
                dummy = SensorReadings(0, 0, 0, 0, 0)
                writer.writerow(dummy.csv_header)

    def generate_and_pass_data(self):
        """Simulates external receiver hardware capturing telemetry updates."""
        # Generates fresh randomized values for all fields in our dataclass
        new_packet = SensorReadings(
            temperature=random.uniform(18.0, 35.0),
            humidity=random.uniform(30.0, 75.0),
            pressure=random.uniform(980.0, 1030.0),
            voltage=random.uniform(3.1, 5.0),
            air_quality=random.uniform(10.0, 50.0)
        )
        
        # Route data payload direct into user view layer
        self.view.update_display(new_packet)

        # Append streaming readings into targeting file path destinations
        if self.log_file_path:
            try:
                with open(self.log_file_path, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(new_packet.csv_row)
            except IOError as e:
                print(f"Error appending data matrix line blocks to file destinations: {e}")
