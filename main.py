import threading
import queue
import os

import tomllib

from server import Server
from plotter import Plotter, PlotInfo

if __name__ == '__main__':
    # config
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    # save path
    path = config["save"]["path"]
    if not os.path.exists(path):
        os.makedirs(path)

    # queue for data exchange between server and plotter
    data_queue = queue.Queue()

    # server
    server = Server(data_queue)
    ip = config["server"]["ip"]
    port = config["server"]["port"]

    # colors
    colors = {
        "red": config["colors"]["red"],
        "green": config["colors"]["green"],
        "blue": config["colors"]["blue"],
        "yellow": config["colors"]["yellow"],
        "purple": config["colors"]["purple"],
        "black": config["colors"]["black"],
    }

    # plots
    window = int(config["plot"]["time_window"] / config["plot"]["dt"])

    up_left = PlotInfo(
        window=window,
        signals=config["plot"]["upper_left"]["signals"],
        limits=config["plot"]["upper_left"]["limits"],
        title=config["plot"]["upper_left"]["title"],
        y_label=config["plot"]["upper_left"]["ylabel"],
        x_label="Time (s)",
        color=[colors[color] for color in config["plot"]["upper_left"]["colors"]],
    )
    down_left = PlotInfo(
        window=window,
        signals=config["plot"]["lower_left"]["signals"],
        limits=config["plot"]["lower_left"]["limits"],
        title=config["plot"]["lower_left"]["title"],
        y_label=config["plot"]["lower_left"]["ylabel"],
        x_label="Time (s)",
        color=[colors[color] for color in config["plot"]["lower_left"]["colors"]],
    )
    right = PlotInfo(
        window=window,
        signals=config["plot"]["right"]["signals"],
        limits=config["plot"]["right"]["limits"],
        title=config["plot"]["right"]["title"],
        y_label=config["plot"]["right"]["ylabel"],
        x_label="Time (s)",
        color=[colors[color] for color in config["plot"]["right"]["colors"]],
    )
    plotter = Plotter(path, data_queue, [up_left, down_left, right])

    # start server
    server_thread = threading.Thread(target=server.start, args=(ip, port))
    server_thread.start()
    print(f"Server started at {ip}:{port}")

    # start plotter
    try:
        plotter.start()
    except Exception as e:
        server.stop()
        plotter.close()
        raise e
