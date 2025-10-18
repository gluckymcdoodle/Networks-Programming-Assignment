import socket
from threading import Thread
import os


HOST = '127.0.0.1'
PORT = 5000
DOWNLOAD_DIR = 'client_downloads'


class Client:
    def __init__(self, HOST, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))
        print("Connected to server!")
        welcome_msg = self.socket.recv(1024).decode()
        print("Server:", welcome_msg)
        
        Thread(target=self.receive_message, daemon=True).start()
        
        self.send_message()

    
    def send_message(self):
        while True:
            msg = input("You: ").strip()
            if not msg:
                continue
            self.socket.send(msg.encode())
            
            if msg.lower() == "exit":
                print("You have Disconnected.")
                self.socket.close()
                break
            
    def receive_message(self):
        buffer = b""
        in_file_transfer = False
        file_data = b""

        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    print("Server has closed connection.")
                    break

                # Handle file transfers
                if b"Starting file transfer..." in data:
                    in_file_transfer = True
                    file_data = b""
                    continue

                elif b"File transfer ended." in data:
                    in_file_transfer = False
                    filename = input("Enter filename to save (include extension): ")
                    filepath = os.path.join(DOWNLOAD_DIR, filename)
                    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(file_data)
                    print(f"File has been saved. {filepath}")
                    continue

                if in_file_transfer:
                    file_data += data
                else:
                    print("Server:", data.decode())

            except (ConnectionResetError, OSError):
                print("Connection has been lost.")
                break
            
if __name__ == "__main__":
    Client(HOST, PORT)
