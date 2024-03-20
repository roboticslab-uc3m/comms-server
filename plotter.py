import queue
import matplotlib.pyplot as plt
import numpy as np


class DynamicPlotter:
    def __init__(self, data_queue: queue.Queue, window_size: int = 2048) -> None:
        self.data_queue = data_queue
        self.window_size = window_size

        _, self.ax = plt.subplots()

        self.ax.set_autoscale_on(True)
        self.ax.autoscale_view(True, True, True)
        plt.ion()

        self.plots_initialized = False

    def _init_plots(self) -> None:
        if self.plots_initialized:
            return

        self.x_data = {}
        self.y_data = {}
        self.lines = {}

        data = self.data_queue.get()
        for key, _ in data.items():
            self.x_data[key] = np.linspace(0, self.window_size - 1, self.window_size)
            self.y_data[key] = np.zeros(self.window_size)
            self.lines[key], = self.ax.plot(self.x_data[key], self.y_data[key], label=key)

        self.ax.legend()
        self.plots_initialized = True

    def _clear_plots(self) -> None:
        for key in self.lines.keys():
            self.lines[key].remove()
        self.plots_initialized = False

    def start(self) -> None:
        while True:
            if self.data_queue.empty():
                # self._clear_plots()
                continue

            while not self.data_queue.empty():
                self._init_plots()

                data = self.data_queue.get()

                for key, value in data.items():
                    self.y_data[key] = np.append(self.y_data[key][1:], value)
                    self.lines[key].set_ydata(self.y_data[key])

            # Adjust the x-axis to show a sliding window effect
            for key in self.x_data.keys():
                self.x_data[key] = np.roll(self.x_data[key], -1)
                self.x_data[key][-1] = self.x_data[key][-2] + 1
                self.lines[key].set_xdata(self.x_data[key])

            self.ax.relim()  # Recalculate limits
            self.ax.autoscale_view(True, True, True)  # Autoscale
            plt.draw()
            plt.pause(0.001)  # Short pause to allow GUI to update

    def close(self):
        plt.ioff()
        plt.show()
