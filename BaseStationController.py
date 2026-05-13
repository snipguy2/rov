import socket
import logging
import json
from MessageStructs import *
from dataclasses import asdict

#logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format=f'[%(asctime)s - %(levelname)s] - %(message)s',
    filename='app.log',
    filemode='a'  # 'a' for append, 'w' for overwrite
)
logger = logging.getLogger(__name__)


HOST, PORT = "localhost", 9999
dataDictToSend = asdict(PingArduinoMessage())

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(5.0)
    # Connect to the server
    try:
        payload = json.dumps(dataDictToSend).encode('utf-8')
        print(payload)
        sock.connect((HOST, PORT))
        
        # Send data
        sock.sendall(payload + b'\n')
        logger.info(f"Sent:     {payload}")

        # Receive data from the server and shut down
        received = sock.recv(1024)
        logger.info(f"Received: {received.decode().strip()}")
        
    except ConnectionError as e:
        logger.error(f"Connection Error: {e}")

    
        
