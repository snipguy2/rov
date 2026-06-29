import sys
import pygame
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QProgressBar
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPen

# --- CONFIGURATION ---
INPUT_MODE = "KEYBOARD"  # Change to "JOYSTICK" to switch
RAMP_SPEED = 0.05
FRICTION = 0.9
# ---------------------
# 6-DOF Mixing Matrix (6 Inputs: Surge, Sway, Heave, Roll, Pitch, Yaw)
# Order: T1, T2, T3, T4, T5, T6, T7, T8
MIXING_MATRIX = [
#    Su, Sw, He, Ro, Pi, Ya
    [ 1, -1,  0,  0,  0, -1], # T1: Horizontal (+Surge, -Sway, -Yaw)
    [ 1,  1,  0,  0,  0,  1], # T2: Horizontal (+Surge, +Sway, +Yaw)
    [-1, -1,  0,  0,  0,  1], # T3: Horizontal (-Surge, -Sway, +Yaw)
    [-1,  1,  0,  0,  0, -1], # T4: Horizontal (-Surge, +Sway, -Yaw)
    [ 0,  0,  1, -1,  1,  0], # T5: Vertical (+Heave, +Pitch, -Roll)
    [ 0,  0, -1, -1, -1,  0], # T6: Veritcal (-Heave, -Pitch, -Roll)
    [ 0,  0, -1,  1,  1,  0], # T7: Vertical (-Heave, +Pitch, +Roll)
    [ 0,  0,  1,  1,  -1,  0]  # T8: Vertical (+Heave, -Pitch, +Roll)
]

class ROVControlPanel(QGraphicsView):
    def __init__(self):
        super().__init__()
        
        self.pressed_keys = set()
        self.arrows = {}
        
        # Thruster angles for display
        self.thruster_angles_deg = {
            1: -45,   2: 45,    3: 45,   4: 45,     # Horizontals
            5: 90,   6: 270,   7: 270,   8: 90      # Verticals
        }

        # --- Initialize Pygame safely ---
        import os
        # This tells pygame to use a dummy video driver
        os.environ['SDL_VIDEODRIVER'] = 'dummy' 
        pygame.init()
        # -------------------------------------
        
        self.bars = {}
        
        self.scene = QGraphicsScene(0, 0, 600, 600)
        self.setScene(self.scene)
        self.setWindowTitle("BlueROV2 Heavy Live Control")
        
        self.axes = {"surge": 0.0, "sway": 0.0, "heave": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}
        
        # Thruster positions on UI
        self.thruster_map = {
            1: (400, 100), 2: (200, 100), 3: (400, 500), 4: (200, 500),
            5: (500, 200), 6: (100, 200), 7: (500, 400), 8: (100, 400)
        }
        
        self.setup_ui()
        
        if INPUT_MODE == "JOYSTICK":
            pygame.joystick.init()
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.get_inputs = self.get_joystick_inputs
        else:
            self.get_inputs = self.get_keyboard_inputs
            
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_controls)
        self.timer.start(20)

    def keyPressEvent(self, event):
        self.pressed_keys.add(event.key())
        
    def keyReleaseEvent(self, event):
        if event.key() in self.pressed_keys:
            self.pressed_keys.remove(event.key())

    def setup_ui(self):
        self.arrows = {}
        for t_id, (x, y) in self.thruster_map.items():
            # Add Progress Bar
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(50)
            bar.setFixedSize(80, 20)
            proxy = self.scene.addWidget(bar)
            proxy.setPos(x - 40, y)
            self.bars[t_id] = bar
            
            # Create the dynamic yellow line
            line = self.scene.addLine(0, 0, 0, 0, QPen(Qt.GlobalColor.yellow, 3))
            line.setPos(x, y - 30) # Anchor above bar
            self.arrows[t_id] = line
            
    def update_arrows(self, thruster_outputs):
        import math
        for i, val in enumerate(thruster_outputs):
            t_id = i + 1
            line = self.arrows.get(t_id)
            if not line: continue
            
            # 1. Magnitude (Body length)
            mag = abs(val) * 40
            
            # 2. Get angle from config, flip if negative thrust
            base_angle = self.thruster_angles_deg[t_id]
            target_angle = base_angle if val >= 0 else base_angle + 180
            
            # 3. Vector calculation (Qt Y is down, so invert dy)
            rad = math.radians(target_angle)
            dx = math.cos(rad) * mag
            dy = -math.sin(rad) * mag
            
            line.setLine(0, 0, dx, dy)
            
            # 4. Color logic
            color = Qt.GlobalColor.green if val >= 0 else Qt.GlobalColor.red
            line.setPen(QPen(color, 3))
            
    def get_joystick_inputs(self):
        pygame.event.pump()
        # Using a simple deadzone function here
        def d(v, z=0.15): return 0 if abs(v) < z else v
        return [
            d(self.joystick.get_axis(1) * -1), # Surge
            d(self.joystick.get_axis(0)),       # Sway
            d(self.joystick.get_axis(3) * -1),  # Heave
            d(self.joystick.get_axis(2))        # Yaw
        ]

    def get_keyboard_inputs(self):
        # 1. Map your pressed_keys set directly to the targets dictionary
        targets = {"surge": 0, "sway": 0, "heave": 0, "roll": 0, "pitch": 0, "yaw": 0}
        
        if Qt.Key.Key_W in self.pressed_keys: targets["surge"] += 1.0
        if Qt.Key.Key_S in self.pressed_keys: targets["surge"] -= 1.0
        if Qt.Key.Key_A in self.pressed_keys: targets["sway"] -= 1.0
        if Qt.Key.Key_D in self.pressed_keys: targets["sway"] += 1.0
        if Qt.Key.Key_C in self.pressed_keys: targets["heave"] -= 1.0
        if Qt.Key.Key_Space in self.pressed_keys: targets["heave"] += 1.0
        if Qt.Key.Key_R in self.pressed_keys: targets["pitch"] -= 1.0
        if Qt.Key.Key_F in self.pressed_keys: targets["pitch"] += 1.0
        if Qt.Key.Key_E in self.pressed_keys: targets["roll"] += 1.0
        if Qt.Key.Key_Q in self.pressed_keys: targets["roll"] -= 1.0
        if Qt.Key.Key_3 in self.pressed_keys: targets["yaw"] += 1.0
        if Qt.Key.Key_1 in self.pressed_keys: targets["yaw"] -= 1.0
        
        # 2. Update self.axes toward the targets
        for axis in self.axes:
            if targets[axis] != 0:
                # Ramp up towards target
                self.axes[axis] += targets[axis] * RAMP_SPEED
            else:
                # Decaying to rest
                self.axes[axis] *= FRICTION
                if abs(self.axes[axis]) < 0.001:
                    self.axes[axis] = 0.0
            
            # Clamp values
            self.axes[axis] = max(min(self.axes[axis], 1.0), -1.0)
        
        return [self.axes["surge"], self.axes["sway"], self.axes["heave"], 
                self.axes["roll"], self.axes["pitch"], self.axes["yaw"]]
        
    def apply_deadzone(self, val, zone=0.15):
        return 0 if abs(val) < zone else val

    def update_controls(self):
        # 1. Fetch current inputs (Keyboard or Joystick)
        inputs = self.get_inputs() # Returns [surge, sway, heave, yaw]
        
        # 2. Calculate raw outputs using the Mixing Matrix
        raw_outputs = []
        for row in MIXING_MATRIX:
            # zip(inputs, row) pairs your 4 inputs with the 4 coefficients for that thruster
            val = sum(input_val * coeff for input_val, coeff in zip(inputs, row))
            raw_outputs.append(val)
            
        # 3. Normalize if we exceed the limit (1.0)
        max_val = max([abs(v) for v in raw_outputs] + [1.0]) # +[1.0] prevents div by zero
        outputs = [v / max_val for v in raw_outputs]

        # Update Dynamic arrows
        self.update_arrows(outputs)

        # 4. Update Bars
        for i, val in enumerate(outputs):
            # Mapping -1.0..1.0 to 0..100
            display_val = int((val + 1) * 50)
            
            # Ensure the bar exists before updating
            if (i + 1) in self.bars:
                self.bars[i + 1].setValue(display_val)
                
                # Dynamic Coloring
                if display_val > 55:
                    self.bars[i+1].setStyleSheet("QProgressBar::chunk { background-color: #00FF00; }")
                elif display_val < 45:
                    self.bars[i+1].setStyleSheet("QProgressBar::chunk { background-color: #FF0000; }")
                else:
                    self.bars[i+1].setStyleSheet("QProgressBar::chunk { background-color: #008000; }")
                    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ROVControlPanel()
    window.show()
    sys.exit(app.exec())