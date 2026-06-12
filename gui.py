from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QApplication,
    QVBoxLayout, QLabel, QGridLayout,
    QPushButton, QFrame, QHBoxLayout
)

from PyQt6.QtCore import(
    pyqtSignal, QThread, Qt, QObject
)

from PyQt6.QtGui import(
    QImage, QPixmap
)

import cv2
import logging, sys, os, time
logger = logging.getLogger(__name__)


# Force FFmpeg to use TCP for RTSP streams
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|rtsp_flags;listen'
STREAM_URL = 'tcp://localhost:1234' 

logger.info("Starting...")

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setCentralWidget(StreamWindow(self))
        
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
        
    
class SensorDataWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout()
        self.create_widgets()
        self.apply_layout()
        
    def create_widgets(self):
        self.leakSensorDisplay = LeakSensorDisplay()
        
class LeakSensorDisplay(QWidget):
    def __init__(self, numSensors:int, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.numSensors = numSensors
        self.create_widgets()
        self.setup_signals()
        self.apply_layout()
        
    def create_widgets(self):
        self.sensorLabelPairs = []
        for sensor in range(self.numSensors):
            sensorName = QLabel(f"Leak Sensor {sensor}")
            sensorData = QLabel("N/A")
            self.sensorLabelPairs.append((sensorName, sensorData))
        
    def read_in_sensor_data(self, dataDict):
        dataDict["Special"] = "Great"
        
    def setup_signals(self):
        pass
    
    def apply_layout(self):
        for sensor in self.sensorLabelPairs:
            self.layout.addWidget(sensor[0])
            self.layout.addWidget(sensor[1])
            
        self.setLayout(self.layout)
        
class LeakSensorDisplayPair(QWidget):
    def __init__(self, name:str, parent=None):
        super().__init__(parent)
        self.label = QLabel(f"{name}:")
        self.value = QLabel("")
    
    def update_label(self, newValue:str):
        self.value.setText(newValue)
        
        
#==========MVC Example=====================

class MyController(QObject):
    def __init__(self, model, view, parent=None):
        super().__init__(parent)
        self._model = model
        self._view = view

        # Connect model's dataChanged signal to view's update slot
        self._model.dataChanged.connect(self._view.update_label_text)

    def change_data(self, new_data):
        self._model.text = new_data # Update the model, which will trigger view update

class MyModel(QObject):
    dataChanged = pyqtSignal(str) # Signal to emit when data changes

    def __init__(self, initial_text="Initial Text"):
        super().__init__()
        self._text = initial_text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        if self._text != new_text:
            self._text = new_text
            self.dataChanged.emit(self._text) # Emit signal on change

class MyView(QLabel):
    def __init__(self, parent=None):
        super().__init__("Loading...", parent) # Initial text

    def update_label_text(self, new_text):
        self.setText(new_text)

#======================
        
def main():
    app = QApplication(sys.argv)
    root = MainWindow()
    root.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()