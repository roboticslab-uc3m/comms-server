import socket
import queue
import json


def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return e
    return wrapper


class Server:
    def __init__(self, data_queue: queue.Queue) -> None:
        self.socket = None
        self.data_queue = data_queue

    @exception_handler
    def start(self, host: str, port: int) -> Exception | None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host, port))

        while True:
            data, _ = self.socket.recvfrom(4096)
            self.data_queue.put(json.loads(data.decode('utf-8')))

    def stop(self) -> None:
        if not self.socket:
            return

        self.socket.close()
        self.socket = None
