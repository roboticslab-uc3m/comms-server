import queue
import matplotlib.pyplot as plt
import numpy as np


class DynamicPlotter:
    def __init__(self, data_queue: queue.Queue, window_size: int = 19200) -> None:
        self.data_queue = data_queue
        self.window_size = window_size

        _, self.ax = plt.subplots(1, 2, figsize=(30, 20))

        x = np.zeros(window_size)
        self.control_signal_y = np.zeros(window_size)
        self.control_signal_line, = self.ax[0].plot(x, self.control_signal_y, label="control_signal")

        self.reference_y = np.zeros(window_size)
        self.reference_line, = self.ax[1].plot(x, self.reference_y, label="reference")

        self.position_y = np.zeros(window_size)
        self.position_line, = self.ax[1].plot(x, self.position_y, label="position")

        self.time_elapsed = np.zeros(window_size)

        self.ax[0].set_ylim(0, 4)
        self.ax[1].set_ylim(0, 40_000)

        for i in range(2):
            self.ax[i].legend()
            self.ax[i].autoscale_view(True, True, False)

        plt.ion()

        self.disconnected_counter = 0

    def _reset_plots(self) -> None:
        x = np.zeros(self.window_size)
        y = np.zeros(self.window_size)

        self.time_elapsed = x
        self.reference_y = y
        self.position_y = y
        self.control_signal_y = y

        self.reference_line.set_xdata(x)
        self.reference_line.set_ydata(y)

        self.position_line.set_xdata(x)
        self.position_line.set_ydata(y)

        self.control_signal_line.set_xdata(x)
        self.control_signal_line.set_ydata(y)

    def start(self) -> None:
        while True:
            if self.data_queue.empty():
                self.disconnected_counter += 1
                if self.disconnected_counter > 100_000:
                    self._reset_plots()

                continue

            while not self.data_queue.empty():
                self.disconnected_counter = 0

                data = self.data_queue.get()

                self.reference_y = np.append(self.reference_y[1:], data["reference"])
                self.reference_line.set_ydata(self.reference_y)

                self.position_y = np.append(self.position_y[1:], data["position"])
                self.position_line.set_ydata(self.position_y)

                self.control_signal_y = np.append(self.control_signal_y[1:], data["resistance"])
                self.control_signal_line.set_ydata(self.control_signal_y)

                self.time_elapsed = np.append(self.time_elapsed[1:], data["time"])

                self.reference_line.set_xdata(self.time_elapsed)
                self.position_line.set_xdata(self.time_elapsed)
                self.control_signal_line.set_xdata(self.time_elapsed)

            for i in range(2):
                self.ax[i].relim()
                self.ax[i].autoscale_view(True, True, False)

            plt.draw()
            plt.pause(0.001)  # Short pause to allow GUI to update

    def close(self):
        plt.ioff()
        plt.close()
