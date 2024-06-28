import datetime
import queue
from dataclasses import dataclass

from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd

from vclog import Logger


logger = Logger("server")


@dataclass
class PlotInfo:
    window: int
    signals: list[str]
    limits: tuple[float, float]
    title: str
    y_label: str
    x_label: str
    color: list[str]


@dataclass
class AxInfo:
    t: np.ndarray
    ys: list[np.ndarray]
    ax: Axes
    lines: list
    signals: list[str]

    def update_time(self, t: float) -> None:
        self.t = np.append(self.t[1:], t)
        for l in self.lines:
            l.set_xdata(self.t)

    def update_y(self, y: list[float]) -> None:
        for i, l in enumerate(self.lines):
            self.ys[i] = np.append(self.ys[i][1:], y[i])
            l.set_ydata(self.ys[i])

    def update(self) -> None:
        self.ax.relim()
        self.ax.autoscale_view(True, True, True)

    def clear(self) -> None:
        self.t = np.zeros_like(self.t)

        for i in range(len(self.signals)):
            self.ys[i] = np.zeros_like(self.ys[i])
            self.lines[i].set_ydata(self.ys[i])
            self.lines[i].set_xdata(self.t)


class Data:
    def __init__(self) -> None:
        self.data: dict[str, list[float]] = {}

    def extend(self, d: dict[str, float]) -> None:
        for k, v in d.items():
            if k in self.data:
                self.data[k].append(v)
            else:
                self.data[k] = [v]

    def clear(self) -> None:
        self.data.clear()

    def __getitem__(self, key: str) -> float:
        try:
            return self.data[key][-1]
        except:
            logger.warning(f"unknown key {key}")
            return 0.0

    def __bool__(self) -> bool:
        return bool(self.data)


class Plotter:
    def __init__(self,
                 data_queue: queue.Queue,
                 plot_info_list: list[PlotInfo],
                 ) -> None:
        self.data_queue = data_queue
        self.data = Data()
        self.timeout = 0
        self.client_connected = False

        plt.figure(figsize=(30, 20))
        gs = gridspec.GridSpec(2, 2, width_ratios=[0.45, 0.55])

        self.up_left_ax = self._init_ax(plot_info_list[0], gs, 0)
        self.down_left_ax = self._init_ax(plot_info_list[1], gs, 1)
        self.right_ax = self._init_ax(plot_info_list[2], gs, 2)

        plt.ion()

    def _init_ax(self, plot_info: PlotInfo, gs: gridspec.GridSpec, position: int) -> AxInfo:
        match position:
            case 0:
                ax = plt.subplot(gs[0, 0])
            case 1:
                ax = plt.subplot(gs[1, 0])
            case 2:
                ax = plt.subplot(gs[:, 1])
            case _:
                raise ValueError("wrong number of plots")

        n_signals = len(plot_info.signals)
        t = np.zeros(plot_info.window)
        y = np.zeros(plot_info.window)

        lines = []
        ys = []
        for i in range(n_signals):
            line, = ax.plot(t, y, label=plot_info.signals[i], color=plot_info.color[i])
            lines.append(line)
            ys.append(y)

        ax.set_title(plot_info.title)
        ax.set_ylabel(plot_info.y_label)
        ax.set_xlabel(plot_info.x_label)
        ax.set_ylim(*plot_info.limits)
        ax.legend()
        ax.autoscale_view(True, True, True)

        return AxInfo(t, ys, ax, lines, plot_info.signals)

    def start(self) -> None:
        while True:
            self._start()

    def _is_client_connected(self) -> bool:
        if self.data_queue.empty() and not self.client_connected:
            return False

        if self.data_queue.empty():
            self.timeout += 1
        else:
            self.timeout = 0

        if self.timeout > 100:
            return False

        return True

    def _start(self) -> None:
        # check client connection
        client_connected: bool = self._is_client_connected()

        # reset plots and save data if the client just disconnected
        if not client_connected and self.client_connected:
            date = datetime.datetime.now().strftime("%d-%m-%Y@%H:%M:%S")
            logger.info(f"client is no longer detected: {date}")
            self.save()

            self.up_left_ax.clear()
            self.down_left_ax.clear()
            self.right_ax.clear()

            self.client_connected = False

        # update client connection status
        if client_connected and not self.client_connected:
            date = datetime.datetime.now().strftime("%d-%m-%Y@%H:%M:%S")
            logger.info(f"client is detected: {date}")
            self.client_connected = True

        # do not update plots if there is no client
        if not client_connected and not self.client_connected:
            return

        # get all data from the queue
        while not self.data_queue.empty():
            self.data.extend(self.data_queue.get())

            # update the plots
            self.up_left_ax.update_time(self.data["time"])
            self.up_left_ax.update_y([self.data[s] for s in self.up_left_ax.signals])

            self.down_left_ax.update_time(self.data["time"])
            self.down_left_ax.update_y([self.data[s] for s in self.down_left_ax.signals])

            self.right_ax.update_time(self.data["time"])
            self.right_ax.update_y([self.data[s] for s in self.right_ax.signals])

        # update plot
        self.up_left_ax.update()
        self.down_left_ax.update()
        self.right_ax.update()

        plt.draw()
        plt.pause(0.001)

    def save(self) -> None:
        if not self.data:
            return

        date = datetime.datetime.now().strftime("%d-%m-%Y@%H:%M:%S")
        filename = f"tests/{date}.csv"
        pd.DataFrame(self.data.data).to_csv(filename, index=False)
        logger.info(f"Saved file as {filename}")

        self.data.clear()

    def close(self):
        plt.ioff()
        plt.close()
