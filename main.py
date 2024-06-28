import threading
import queue
from server import Server
from plotter import Plotter, PlotInfo

if __name__ == '__main__':
    # queue for data exchange between server and plotter
    data_queue = queue.Queue()

    # server
    server = Server(data_queue)
    host = "163.117.150.172"
    # host = "localhost"
    port = 8080

    # plotter
    red = "#cf7171"
    green = "#dbe8c1"
    blue = "#aecdd2"
    yellow = "#fadf7f"
    purple = "#c696bc"
    black = "#4d5359"

    window = 10_000

    up_left = PlotInfo(
        window=window,
        signals=["master_control", "control"],
        limits=(0, 101),
        title="Control signal (PWM)",
        y_label="PWM (%)",
        x_label="Time (s)",
        color=[yellow, blue],
    )
    down_left = PlotInfo(
        window=window,
        signals=["resistance"],
        limits=(0, 3.4),
        title="Resistance",
        y_label="Resistance (Ohm)",
        x_label="Time (s)",
        color=[purple],
    )
    right = PlotInfo(
        window=window,
        signals=["position", "reference", "model"],
        limits=(0, 41_000),
        title="Position",
        y_label="Position (ticks)",
        x_label="Time (s)",
        color=[green, red, black],
    )
    plotter = Plotter(data_queue, [up_left, down_left, right])

    # start server
    server_thread = threading.Thread(target=server.start, args=(host, port))
    server_thread.start()
    print(f"Server started at {host}:{port}")

    # start plotter
    try:
        plotter.start()
    except Exception as e:
        server.stop()
        plotter.close()
        raise e
