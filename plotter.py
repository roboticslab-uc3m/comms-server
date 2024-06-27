import time
import datetime
import queue
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class DynamicPlotter:
    def __init__(self, data_queue: queue.Queue, window_size: int = 19200) -> None:
        self.data_queue = data_queue
        self.window_size = window_size
        self.stored_data = {}
        self.data_initialized = False
        self.disconnected_counter = 0
        self.saved_data = False

        _, self.ax = plt.subplots(1, 2, figsize=(30, 20))

        x = np.zeros(window_size)
        # LEFT
        self.control_signal_y = np.zeros(window_size)
        self.control_signal_line, = self.ax[0].plot(x, self.control_signal_y, label="control_signal")

        self.control_signal_2_y = np.zeros(window_size)
        self.control_signal_2_line, = self.ax[0].plot(x, self.control_signal_2_y, label="resistance")
        self.ax[0].set_ylabel("Resistance (\u03A9)")
        self.ax[0].set_xlabel("Time (s)")

        # RIGHT
        self.reference_y = np.zeros(window_size)
        self.reference_line, = self.ax[1].plot(x, self.reference_y, label="reference")

        self.position_y = np.zeros(window_size)
        self.position_line, = self.ax[1].plot(x, self.position_y, label="position")

        self.time_elapsed = np.zeros(window_size)

        self.ax[0].set_ylim(0, 3.3)
        # self.ax[1].set_ylim(0, 45_000)

        for i in range(2):
            self.ax[i].legend()
            self.ax[i].autoscale_view(True, True, True)

        plt.ion()

    def _reset_plots(self) -> None:
        x = np.zeros(self.window_size)
        y = np.zeros(self.window_size)

        self.time_elapsed = x
        self.reference_y = y
        self.position_y = y
        # self.control_signal_y = y

        self.reference_line.set_xdata(x)
        self.reference_line.set_ydata(y)

        self.position_line.set_xdata(x)
        self.position_line.set_ydata(y)

        # self.control_signal_line.set_xdata(x)
        # self.control_signal_line.set_ydata(y)

        self.control_signal_2_line.set_xdata(x)
        self.control_signal_2_line.set_xdata(x)

    def start(self) -> None:
        while True:
            if self.data_queue.empty():
                self.disconnected_counter += 1
                time.sleep(0.001)
                if self.disconnected_counter > 1_000 and not self.saved_data:
                    print("Client is no longer detected")
                    self._reset_plots()
                    self.save()
                    self.saved_data = True
                    self.data_initialized = False

                continue

            while not self.data_queue.empty():
                self.disconnected_counter = 0
                self.saved_data = False

                if not self.data_initialized:
                    data = self.data_queue.get()
                    for key, value in data.items():
                        self.stored_data[key] = np.array([])

                    for key, value in data.items():
                        array = self.stored_data[key]
                        self.stored_data[key] = np.append(array, value)

                    self.data_initialized = True

                data = self.data_queue.get()

                for key, value in data.items():
                    array = self.stored_data[key]
                    self.stored_data[key] = np.append(array, value)

                self.reference_y = np.append(self.reference_y[1:], data["reference"])
                self.reference_line.set_ydata(self.reference_y)

                self.position_y = np.append(self.position_y[1:], data["position"])
                self.position_line.set_ydata(self.position_y)

                self.control_signal_y = np.append(self.control_signal_y[1:], data["master_control"]/100)
                self.control_signal_line.set_ydata(self.control_signal_y)

                # voltage = data["resistance"]
                # resistance = 150*voltage/(3.3-voltage)
                resistance = data["resistance"]
                self.control_signal_2_y = np.append(self.control_signal_2_y[1:], resistance)
                self.control_signal_2_line.set_ydata(self.control_signal_2_y)

                self.time_elapsed = np.append(self.time_elapsed[1:], data["time"])

                self.reference_line.set_xdata(self.time_elapsed)
                self.position_line.set_xdata(self.time_elapsed)
                self.control_signal_line.set_xdata(self.time_elapsed)
                self.control_signal_2_line.set_xdata(self.time_elapsed)

            for i in range(2):
                self.ax[i].relim()
                self.ax[i].autoscale_view(True, True, True)

            plt.draw()
            plt.pause(0.001)

    def save(self) -> None:
        filename = f"tests/{datetime.datetime.now()}.csv".replace(" ", "_")
        if self.stored_data:
            pd.DataFrame(self.stored_data).to_csv(filename, index=False)
            print(f"Saved file as {filename}")
            self.stored_data.clear()

    def close(self):
        plt.ioff()
        plt.close()
