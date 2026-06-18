# main.py
import sys
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QWidget, QMainWindow
from models import SensorReadings
from views import SensorMonitorWidget, StreamWindow
from controllers import TelemetryController


class MainApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.create_widgets()
        self.apply_layout()

    def create_widgets(self):
        self.sensorDisplay = SensorMonitorWidget(SensorReadings)
        self.cameraDisplay = StreamWindow(self)
        self.telementryController = TelemetryController(self.sensorDisplay)

    def apply_layout(self):
        self.layout.addWidget(self.cameraDisplay)
        self.layout.addWidget(self.sensorDisplay)
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
