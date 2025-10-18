
import socket
from threading import Thread, Lock
from datetime import datetime
import os

MAX_CLIENTS = 3
HOST = '127.0.0.1'
PORT = 5000
REPO_DIR = 'server_repo'


class Server:
    def __init__(self, HOST, PORT):
        self.host = HOST
        self.port = PORT
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server has started listening on {self.host}, {self.port}")
        
        self.clients = {}
        self.client_count = 0
        self.lock = Lock()
        self.accept_clients()
        
    def accept_clients(self):
        #accept up to 3 clients, or (MAX_CLIENTS)
        while True:
            if len(self.clients) < MAX_CLIENTS:
                client_socket, address = self.server_socket.accept()
                with self.lock:
                    self.client_count += 1
                    client_name = f"Client{self.client_count:02d}"
                    self.clients[client_socket] = {
                        'name': client_name,
                        'connect_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'disconnect_time': None
                    }
                    print(f"{client_name} has connected from {address}")
                    client_socket.send(f"Welcome {client_name}!".encode())
                    
                    Thread(target=self.handle_client, args = (client_socket,)).start()
            else:
                print("Server is full")
    def handle_client(self, client_socket):
        client_name = self.clients[client_socket]['name']
        #check for keywords
        while True:
            try:
                msg = client_socket.recv(1024).decode().strip()
                if not msg:
                    break
                if msg.lower() == "exit":
                    self.disconnect_client(client_socket)
                    break
                if msg.lower() == "status":
                    status_info = self.get_status()
                    client_socket.send(status_info.encode())
                elif msg.lower() == "list":
                    files = os.listdir(REPO_DIR) if os.path.exists(REPO_DIR) else []
                    if files:
                        file_list = "\n".join(files)
                    else:
                        file_list = "No files in repository"
                    client_socket.send(file_list.encode())
                elif os.path.exists(os.path.join(REPO_DIR, msg)):
                    self.send_file(client_socket, msg)
                else:
                    ack_message = f"{msg} ACK"
                    client_socket.send(ack_message.encode())
            except (ConnectionResetError, ConnectionAbortedError):
                self.disconnect_client(client_socket)
                break
            except Exception as e:
                print(f"ERROR {e}")
                break
    def get_status(self):
        info = []
        with self.lock:
            for data in self.clients.values():
                line = f"{data['name']} | Connected: {data['connect_time']} | Disconnected: {data['disconnect_time'] or 'Active'}"
                info.append(line)
        return "\n".join(info)
    def send_file(self, client_socket, filename):
        filepath = os.path.join(REPO_DIR, filename)
        try:
            with open(filepath, 'rb') as f:
                client_socket.send(b"Starting file transfer...")
                while chunk := f.read(1024):
                    client_socket.send(chunk)
                client_socket.send(b"File transfer ended.")
            print(f"Sent file {filename}")
        except Exception as e:
            client_socket.send(f"Error sending file {e}".encode())
    def disconnect_client(self, client_socket):
        with self.lock:
            client_info = self.clients.get(client_socket, {})
            if client_info:
                client_info['disconnect_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Disconnected {client_info['name']}")
        try:
            client_socket.close()
        except:
            pass
                    
if __name__ == "__main__":
    if not os.path.exists(REPO_DIR):
        os.mkdir(REPO_DIR)
    Server(HOST, PORT)
