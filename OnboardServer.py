import socketserver
import logging
import LoggerUtilities
import json
import ArdunioInterface
import time
from MessageNames import *

#Logging configurations
#===================================
logging.basicConfig(
    level=logging.DEBUG,
    format=f'[%(asctime)s - %(levelname)s] - %(message)s',
    filename='app.log',
    filemode='a'  # 'a' for append, 'w' for overwrite
)
#===================================


EMULATION_MODE = False #set to false if working with real hardware

logger = logging.getLogger(__name__)
conLogger = LoggerUtilities.create_file_logger("ConnectionLogger", "connection.log", f'[%(asctime)s - %(levelname)s] - %(message)s',logging.INFO)

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.arduino = ArdunioInterface.ArdunioMega()
        # Read from socket and handle messages
        while True:
            data = self.request.recv(1024).strip().decode('utf-8')
            if data:
                message = json.loads(data)
                print(f"Received: {message}")
                
                #if message["name"] == "PING_ARDUINO":
                    #arduino.send_message("1")
                self.resolve_arduino_message(message["name"], message)
                
                # Send JSON response with newline delimiter
                response = json.dumps({"status": "ok"}).encode('utf-8')
                self.request.sendall(response + b'\n')
                
    def resolve_arduino_message(self, messageName:str, payload):
        message_map = {
            initBarSensorMessageName:       self.handleInitBarSensorMessage,
            pingArduinoMessageName:         self.handlePingArduinoMessage
        }
        
        if messageName not in message_map.keys():
            return
        
        return message_map[messageName](payload)
    
    def handleInitBarSensorMessage(self, payload):
        print(f"==> Sending INIT_BAR_SENSOR to ardunio...")
        print(f"==> Payload Sent: {payload}")
        
    def handlePingArduinoMessage(self, payload):
        print(f"==> Sending PING_ARDUINO to ardunio...")
        self.arduino.send_message("1")
        
    def handleBar30DataMessage(self, payload):
        print(f"==> Sending BAR_30_DATA to ardunio...")
        print(f"==> Payload Sent: {payload}")
    

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# Run server
if __name__ == "__main__":
    #Create server and bind to host & port 9999
    if EMULATION_MODE:
        HOST, PORT = "localhost", 9999
    else:
        HOST, PORT = "0.0.0.0", 9999
        
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    server.serve_forever()
