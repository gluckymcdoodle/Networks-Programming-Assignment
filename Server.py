
import socket
from threading import Thread, Lock
from datetime import datetime
import os
import time

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
            client_socket, address = self.server_socket.accept()
            with self.lock:
                if len(self.clients) >= MAX_CLIENTS:
                    print(f"Rejected connection from {address}, server  is full")
                    client_socket.send(b"Server is full. Try again later.")
                    client_socket.close()
                    continue

                self.client_count += 1
                client_name = f"Client{self.client_count:02d}"
                self.clients[client_socket] = {
                    'name': client_name,
                    'connect_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'disconnect_time': None
                }
            print(f"{client_name} has connected from {address}")
            client_socket.send(f"Welcome {client_name}!".encode())
            Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        file_request_instance = False
        client_name = self.clients[client_socket]['name']
        try:
            while True:
                msg = client_socket.recv(1024).decode().strip()
                if not msg:
                    break
                if msg.lower() == "exit":
                    break
                elif msg.lower() == "status":
                    status_info = self.get_status()
                    client_socket.send(status_info.encode())

                elif msg.lower() == "list":
                    files = os.listdir(REPO_DIR) if os.path.exists(REPO_DIR) else []
                    file_list = "\n".join(files) if files else "No files in repository"
                    client_socket.send(file_list.encode())
                    file_request_instance = True
                elif file_request_instance:

                    filepath = os.path.join(REPO_DIR, msg)
                    if os.path.exists(filepath):
                        self.send_file(client_socket, msg)
                    else:
                        client_socket.send(f"ERROR: File '{msg}' not found.".encode())
                    file_request_instance = False
                else:
                    client_socket.send(f"{msg} ACK".encode())



        except Exception as e:
            print(f"Error handling {client_name}: {e}")

        finally:
            # only run this once when the loop breaks
            self.disconnect_client(client_socket)

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
            if not os.path.exists(filepath):
                client_socket.send(f"Error: File '{filename}' not found".encode())
                return
            time.sleep(0.1)
            start_msg = f"STARTFILE:{filename}"
            client_socket.send(start_msg.encode())

            with open(filepath, 'rb') as f:
                while chunk := f.read(1024):
                    client_socket.send(chunk)

            time.sleep(0.1)
            client_socket.send(b"ENDFILE")
            print(f"Sent file {filename}")

        except Exception as e:
            error_message = f"Error sending file: {str(e)}"
            client_socket.send(error_message.encode())
            print(error_message)
    def disconnect_client(self, client_socket):
        with self.lock:
            if client_info := self.clients.pop(client_socket, None):
                client_info['disconnect_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Disconnected {client_info['name']}")
        try:
            client_socket.close()
        except Exception:
            pass
                    
if __name__ == "__main__":
    if not os.path.exists(REPO_DIR):
        os.mkdir(REPO_DIR)
    Server(HOST, PORT)
