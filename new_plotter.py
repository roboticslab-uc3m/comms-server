import time
import datetime
import queue
from dataclasses import dataclass
from typing import Any

from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd


@dataclass
class PlotInfo:
    window: int
    signals: list[str]
    limits: tuple[float, float]
    title: str
    y_label: str
    x_label: str


@dataclass
class AxInfo:
    t: np.ndarray
    y: np.ndarray
    ax: Axes
    line: Any
    signals: list[str]

    def update_time(self, t: float) -> None:
        self.t = np.append(self.t[:1], t)
        self.line.set_xdata(self.t)

    def update_y(self, y: float) -> None:
        self.y = np.append(self.y[:1], y)
        self.line.set_ydata(self.y)

    def update(self) -> None:
        self.ax.relim()
        self.ax.autoscale_view(True, True, True)

    def clear(self) -> None:
        self.t = np.zeros_like(self.t)
        self.y = np.zeros_like(self.y)

        self.line.set_xdata(self.t)
        self.line.set_ydata(self.y)


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
            print(f"unknown key {key}")
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

        plt.figure(figsize=(30, 20))
        gs = gridspec.GridSpec(2, 2, width_ratios=[1.5, 1.5])

        self.up_left_ax = self._init_ax(plot_info_list[0], gs, 0)
        self.down_left_ax = self._init_ax(plot_info_list[1], gs, 1)
        self.right_ax = self._init_ax(plot_info_list[2], gs, 2)

        plt.ion()

    def _init_ax(self, plot_info: PlotInfo, gs: gridspec.GridSpec, position: int) -> AxInfo:
        match position:
            case 0:
                ax = plt.subplot(gs[:, 0])
            case 1:
                ax = plt.subplot(gs[0, 1])
            case 2:
                ax = plt.subplot(gs[1, 1])
            case _:
                raise ValueError("wrong number of plots")

        t = np.zeros(plot_info.window)
        y = np.zeros(plot_info.window)

        line, = ax.plot(t, y, label=plot_info.signals[0])
        ax.set_title(plot_info.title)
        ax.set_ylabel(plot_info.y_label)
        ax.set_xlabel(plot_info.x_label)
        ax.set_ylim(*plot_info.limits)
        ax.legend()
        ax.autoscale_view(True, True, True)

        return AxInfo(t, y, ax, line, plot_info.signals)

    def start(self) -> None:
        while True:
            self._start()

    def _is_client_connected(self) -> bool:
        if self.data_queue.empty():
            self.timeout += 1
            time.sleep(0.001)

        if self.timeout > 1000:
            return False

        return True

    def _start(self) -> None:
        # check client connection
        client_connected: bool = self._is_client_connected()

        # reset plots if there is no client
        if not client_connected:
            print("client is no longer detected")
            self.up_left_ax.clear()
            self.down_left_ax.clear()
            self.right_ax.clear()

        # save data when the client disconnects
        if not client_connected and self.data:
            self.save()

        # only continue if there is something to plot
        if self.data_queue.empty():
            return

        self.timeout = 0

        # get data and store it
        self.data.extend(self.data_queue.get())

        # update the plots
        self.up_left_ax.update_time(self.data["time"])
        self.up_left_ax.update_y(self.data[self.up_left_ax.signals[0]])  # TMP

        self.down_left_ax.update_time(self.data["time"])
        self.down_left_ax.update_y(self.data[self.down_left_ax.signals[0]])  # TMP

        self.right_ax.update_time(self.data["time"])
        self.right_ax.update_y(self.data[self.right_ax.signals[0]])  # TMP

        # update plot
        self.up_left_ax.update()
        self.down_left_ax.update()
        self.right_ax.update()

        plt.draw()
        plt.pause(0.001)

    def save(self) -> None:
        filename = f"tests/{datetime.datetime.now()}.csv".replace(" ", "_")
        pd.DataFrame(self.data).to_csv(filename, index=False)
        print(f"Saved file as {filename}")
        self.data.clear()

    def close(self):
        plt.ioff()
        plt.close()
