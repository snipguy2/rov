# definitions for qt models
from PyQt6.QtCore import (
    QObject, pyqtSignal, Qt,
    QAbstractListModel
)

from PyQt6.QtWidgets import (
    QLabel, QFrame, QSpacerItem, QGridLayout,
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QSizePolicy, QGridLayout, QMainWindow,
    QListView
)

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



#=================================


if __name__ == "__main__":
    app = QApplication([])

    # Create Model, View, and Controller instances
    model = MyModel("Hello, MVC!")
    view = MyView()
    controller = MyController(model, view)

    # Set up a simple UI to demonstrate
    window = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(view)

    button1 = QPushButton("Change to 'World!'")
    button1.clicked.connect(lambda: controller.change_data("World!"))
    layout.addWidget(button1)

    button2 = QPushButton("Change to 'PyQt MVC'")
    button2.clicked.connect(lambda: controller.change_data("PyQt MVC"))
    layout.addWidget(button2)

    window.setLayout(layout)
    window.show()

    # Initial update of the view based on the model's initial state
    view.update_label_text(model.text)
    
    (app.exec())
