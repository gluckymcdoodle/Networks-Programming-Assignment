import socket
from threading import Thread
import os
import time


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
            time.sleep(0.05)
            if not msg:
                continue
            self.socket.send(msg.encode())
            
            if msg.lower() == "exit":
                print("You have Disconnected.", flush=True)
                self.socket.close()
                break
            
    def receive_message(self):
        buffer = b""
        in_file_transfer = False
        file_data = b""
        filename = None
            
        while True:
            try:
                data = self.socket.recv(1024)
                if not data:
                    print("Server has closed connection.", flush=True)
                    break

                decoded = None #for binary data
                try:
                    decoded = data.decode()
                except UnicodeDecodeError:
                    pass
                
                #handle file transfers
                if decoded and decoded.startswith("STARTFILE:"):
                    in_file_transfer = True
                    file_data = b""
                    filename = decoded.split(":", 1)[1].strip()
                    print(f"Receiving file: {filename}", flush=True)
                    continue

                elif decoded and decoded == "ENDFILE":
                    in_file_transfer = False
                    if filename:
                        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
                        filepath = os.path.join(DOWNLOAD_DIR, filename)
                        with open(filepath, "wb") as f:
                            f.write(file_data)
                        print(f"File has been saved. {filepath}", flush=True)
                        filename = None
                    continue

                if in_file_transfer:
                    file_data += data
                else:
                    print("Server:", data.decode(), flush=True)

            except OSError:
                print("Connection has been lost.", flush=True)
                break
            
if __name__ == "__main__":
    Client(HOST, PORT)
