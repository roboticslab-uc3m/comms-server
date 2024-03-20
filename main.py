import threading
import queue
from server import TCPServer
from plotter import DynamicPlotter

if __name__ == '__main__':
    data_queue = queue.Queue()

    server = TCPServer(data_queue)
    plotter = DynamicPlotter(data_queue, window_size=1920)

    host = "163.117.150.172"
    port = 8080

    server_thread = threading.Thread(target=server.start, args=(host, port))
    server_thread.start()

    print(f"Server started at {host}:{port}")

    try:
        # This keeps the plotter in the main thread
        plotter.start()
    except Exception as e:
        print(e)
    finally:
        server.stop()
        plotter.close()
