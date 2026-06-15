from PyQt6.QtCore import (
    QObject, pyqtSignal
)
from PyQt6.QtWidgets import (
    QLabel
)
from MessageStructs import *


class LeakSensorDataModel(QObject):
    dataChanged = pyqtSignal(bool)
    
    def __init__(self, initial_leak_status:bool=False):
        super().__init__()
        self._leakPresent:bool = initial_leak_status
        
    @property
    def leakPresent(self):
        return self._leakPresent
    
    @leakPresent.setter
    def leakPresent(self, leak_status):
        if self._leakPresent != leak_status:
            self._leakPresent = leak_status
            self.dataChanged.emit(self._leakPresent) # Emit signal on change


class DepthSensorDataModel(QObject):
    dataChanged = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._temperature: float = -99.99
        self._pressure: float = -99.99
        
    @property
    def temperature(self):
        return self._temperature
    
    @temperature.setter
    def temperature(self, temperature):
        if self._temperature != temperature:
            self._temperature = temperature
            self.dataChanged.emit(self._temperature)
    
    @property
    def pressure(self):
        return self._pressure
    
    @pressure.setter
    def pressure(self, pressure):
        if self._pressure != pressure:
            self._pressure = pressure
            self.dataChanged.emit(self._pressure)

class FluidDensityDataModel(QObject):
    dataChanged = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fluidDensity: float = 997.0
        
    @property
    def fluidDensity(self):
        return self._fluidDensity
    
    @fluidDensity.setter
    def fluidDensity(self, density:float):
        if self._fluidDensity != density:
            self._fluidDensity = density
            self.dataChanged.emit(self._fluidDensity)

            
#===============================
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