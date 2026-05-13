import serial
import time
import serial.tools.list_ports


class ArdunioMega(serial.Serial):
    def __init__(self):
        ports = list(serial.tools.list_ports.grep("USB"))
        super().__init__(port=ports[0].device,baudrate=115200)

    def send_message(self, message):
        # Encode string to bytes ('utf-8') before sending
        self.write(bytes(message, 'utf-8'))
        print(f"Sent: {message}")


def main():
    arduino = ArdunioMega()
    # Mandatory: Wait for Arduino to reset after opening serial port
    time.sleep(2) 

    # Send data
    arduino.send_message("1")  # Example: send "1" to turn LED on

    # Close the port
    arduino.close()
