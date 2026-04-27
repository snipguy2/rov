import socket
import logging

#logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s - %(levelname)s] - %(message)s',
    filename='app.log',
    filemode='a'  # 'a' for append, 'w' for overwrite
)
logger = logging.getLogger(__name__)


HOST, PORT = "localhost", 9999
data = "hello world"

# Create a socket (SOCK_STREAM means a TCP socket)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(5.0)
    # Connect to the server
    try:
        sock.connect((HOST, PORT))
        
        # Send data
        sock.sendall(bytes(data + "\n", "utf-8"))
        logger.info(f"Sent:     {data}")

        # Receive data from the server and shut down
        received = sock.recv(1024)
        logger.info(f"Received: {received.decode().strip()}")
        
    except ConnectionError as e:
        logger.error(f"Connection Error: {e}")

    
        
