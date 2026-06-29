import pygame

# Simplified BlueROV2 Heavy Mixing Matrix Coefficients
# Order: Surge, Sway, Heave, Yaw
# Thrusters 1-8 are typically mapped as:
# 1: Front Right Vertical, 2: Front Left Vertical, 3: Rear Right Vertical, 4: Rear Left Vertical
# 5: Front Right Horizontal, 6: Front Left Horizontal, 7: Rear Right Horizontal, 8: Rear Left Horizontal
MIXING_MATRIX = [
    [ 0,  0,  1,  0], # T1
    [ 0,  0,  1,  0], # T2
    [ 0,  0,  1,  0], # T3
    [ 0,  0,  1,  0], # T4
    [ 1,  1,  0, -1], # T5
    [ 1, -1,  0,  1], # T6
    [ 1, -1,  0, -1], # T7
    [ 1,  1,  0,  1]  # T8
]

def apply_deadzone(value, deadzone=0.1):
    """
    Returns 0.0 if the absolute value is less than the deadzone,
    otherwise rescales the remaining range to 0.0 - 1.0.
    """
    if abs(value) < deadzone:
        return 0.0
    
    # Optional: Rescale the value so that it starts at 0.0 
    # immediately after the deadzone for smoother movement.
    sign = 1 if value > 0 else -1
    return (abs(value) - deadzone) / (1.0 - deadzone) * sign

def get_motor_outputs(inputs):
    """
    inputs: list [surge, sway, heave, yaw] where each is -1.0 to 1.0
    Returns: list of 8 float values
    """
    outputs = []
    for row in MIXING_MATRIX:
        # Dot product of input vector and mixing matrix row
        val = sum(i * m for i, m in zip(inputs, row))
        # Normalize/Clip to -1.0 to 1.0
        outputs.append(max(min(val, 1.0), -1.0))
    return outputs

# --- Main Simulation Loop ---
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

print("Monitoring Thruster Outputs:")

try:
    while True:
        pygame.event.pump()
        
        # Mapping inputs (invert axis if necessary for your controller)
        raw_surge = joystick.get_axis(1) * -1 # Left stick Y
        surge = apply_deadzone(raw_surge, deadzone=0.15)
        raw_sway  = joystick.get_axis(0)       # Left stick X
        sway = apply_deadzone(raw_sway, deadzone=0.15)
        raw_heave = joystick.get_axis(3) * -1  # Right stick Y
        heave = apply_deadzone(raw_heave, deadzone=0.15)
        raw_yaw   = joystick.get_axis(2)       # Right stick X
        yaw = apply_deadzone(raw_yaw, deadzone=0.15)
        
        inputs = [surge, sway, heave, yaw]
        motor_vals = get_motor_outputs(inputs)
        
        
        #print(f"\rRAW: {joystick.get_axis(0):.3f} | CLEAN: {apply_deadzone(joystick.get_axis(0), 0.15):.3f}", end="\n")
        # Display on screen
        print(f"\rT1:{motor_vals[0]:.2f} T2:{motor_vals[1]:.2f} T3:{motor_vals[2]:.2f} T4:{motor_vals[3]:.2f} "
              f"T5:{motor_vals[4]:.2f} T6:{motor_vals[5]:.2f} T7:{motor_vals[6]:.2f} T8:{motor_vals[7]:.2f}", 
              end="")
except KeyboardInterrupt:
    print("\nStopped.")