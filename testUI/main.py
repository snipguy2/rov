# main.py
import sys
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QWidget, QMainWindow
from models import SensorReadings
from views import SensorMonitorWidget, StreamWindow
from controllers import TelemetryController
from control_views import ROVControlPanel

class MainApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.create_widgets()
        self.apply_layout()

    def create_widgets(self):
# 1. Create the view
        self.sensorDisplay = SensorMonitorWidget(SensorReadings)
        self.cameraDisplay = StreamWindow(self)
        
        # 2. Create the controller with the initialized view
        self.telementryController = TelemetryController(self.sensorDisplay)
        
        
        # 3. Explicitly link them
        self.sensorDisplay.controller = self.telementryController
        
        # ... signal connections ...
        self.sensorDisplay.connect_requested.connect(self.telementryController.handle_connection_request)
        
        self.rovControls = ROVControlPanel()
        self.rovControls.thrust_updated.connect(self.telementryController.send_thruster_command)
        
        self.sensorDisplay.connect_requested.connect(self.cameraDisplay.set_stream_ip)

        # ADD THIS DEBUG PRINT to verify the connection exists
        # is_connected = self.sensorDisplay.connect_requested.receivers(self.telementryController.handle_connection_request)
        print("DEBUG: Connection wire established between widget and controller.")

        # Connect the control panel's output signal to the controller's send method
        #self.rovControls.thrust_updated.connect(self.telementryController.send_thruster_command)

    def apply_layout(self):
        self.layout.addWidget(self.cameraDisplay)
        self.layout.addWidget(self.sensorDisplay)
        self.layout.addWidget(self.rovControls)
        self.setLayout(self.layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setCentralWidget(MainApp(self))

def main():
    app = QApplication(sys.argv)
    
    # 1. Initialize view component, passing the class type itself for blueprint construction
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
