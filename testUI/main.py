# main.py
import sys
from PyQt6.QtWidgets import QApplication
from models import SensorReadings
from views import SensorMonitorWidget
from controllers import TelemetryController

def main():
    app = QApplication(sys.argv)
    
    # 1. Initialize view component, passing the class type itself for blueprint construction
    window = SensorMonitorWidget(SensorReadings)
    window.show()
    
    # 2. Wire up the polling driver pipeline to direct target window
    controller = TelemetryController(window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
