import socketserver
import logging

#Logging configurations
#===================================
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s - %(levelname)s] - %(message)s',
    filename='app.log',
    filemode='a'  # 'a' for append, 'w' for overwrite
)
logger = logging.getLogger(__name__)



class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Read from socket and handle messages
        while True:
            self.data = self.request.recv(1024)
            if not self.data:
                break
            # Process data (ideally put into a thread-safe Queue)
            logger.info(f"Received from {self.client_address[0]}: {self.data.decode()}")
            
            # Send back the same data in uppercase to client
            self.request.sendall(self.data.upper())

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# Run server
if __name__ == "__main__":
    #Create server and bind to host "localhost" & port 9999
    HOST, PORT = "localhost", 9999
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    server.serve_forever()
