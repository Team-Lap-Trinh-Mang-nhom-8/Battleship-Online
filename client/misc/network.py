import json
import socket


class Network:
    server = "localhost"
    port = 1234
    address = server, port

    def __init__(
        self,
        sock=None,
    ):
        if sock is None:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.client = sock
        self.connected = False
    
    def connect(self):
        """Connect to the server. Can be called explicitly or will be called automatically on first send/receive."""
        if not self.connected:
            try:
                self.client.connect(self.address)
                self.connected = True
            except ConnectionRefusedError:
                raise ConnectionRefusedError(f"Could not connect to server at {self.address}. Make sure the server is running.")
    
    def ensure_connected(self):
        """Ensure connection is established before operations."""
        if not self.connected:
            self.connect()

    def receive(self):
        self.ensure_connected()
        buff = b""
        n = int.from_bytes(self.client.recv(4)[:4], "big")
        while n > 0:
            b = self.client.recv(n)
            buff += b
            n -= len(b)
        return json.loads(buff.decode())

    def send(self, *data):
        self.ensure_connected()
        if len(data) == 1:
            data = data[0]
        final_data = b""
        data = json.dumps(data)
        final_data += len(data).to_bytes(4, "big")
        final_data += data.encode()
        try:
            self.client.send(final_data)
        except:
            pass

    def close(self):
        self.client.close()
