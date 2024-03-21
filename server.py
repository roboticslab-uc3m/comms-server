import socket
import queue
import threading
import pickle


def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return e
    return wrapper


class TCPServer:
    def __init__(self, data_queue: queue.Queue) -> None:
        self.socket = None
        self.data_queue = data_queue

    @exception_handler
    def start(self, host: str, port: int) -> Exception | None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen()

        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket: socket.socket) -> None:
        with client_socket:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break

                deserialized_data = pickle.loads(data)
                self.data_queue.put(deserialized_data)

    def stop(self) -> None:
        if not self.socket:
            return

        self.socket.close()
        self.socket = None
