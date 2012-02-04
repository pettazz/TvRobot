import transmissionrpc
from config import TRANSMISSION

class TransmissionManager:
    def __init__(self):
        #try to connect to the Transmission server
        self.daemon = transmissionrpc.Client(
            address=TRANSMISSION['server'], 
            port=TRANSMISSION['port'], 
            user=TRANSMISSION['user'], 
            password=TRANSMISSION['password'])

    def __getattr__(self, name):
        return getattr(self.daemon, name)