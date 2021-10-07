import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time


class Plotter:
    def __init__(self, frame):
        # Chart
        self.fig = Figure(figsize=(4, 2), dpi=100)
        self.fig.suptitle("Detection Response Task")
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, padx=2, pady=2, sticky='NEWS')

        self.plt = list()

        self.ports = set()

        # Plot time
        self.time_array = np.arange(-60, 0, .1)

        # Plot tic
        self.next_update = time.time()
        self.interval = .1

        # Reaction Time
        self.rt_now = dict()
        self.rt_array = dict()
        self.rt_xy = dict()
        self.plot_lines = set()

        self.rt_y_min = 0
        self.rt_y_max = 2

        # Stimulus State
        self.state_now = dict()
        self.state_array = dict()
        self.state_xy = dict()

        # Animation
        self.run = False
        self.ani = None

    def add_rt_plot(self, title, y_label):
        self.plt.append(self.fig.add_subplot(212))
        # Y axes
        self.plt[0].set_ylabel(y_label)
        self.plt[0].yaxis.set_label_position('right')
        self.plt[0].yaxis.set_tick_params()

    def add_state_plot(self, y_label):
        self.plt.append(self.fig.add_subplot(211))

        # X axes
        self.plt[1].xaxis.set_tick_params(labelbottom=False)
        # Y axes
        self.plt[1].set_ylabel(y_label)
        self.plt[1].yaxis.set_label_position('right')
        self.plt[1].set_ylim([-0.2, 1.2])
        self.plt[1].set_yticks([0, 1])
        self.plt[1].set_yticklabels(["Off", "On"])
        # self.plt[1].yaxis.set_tick_params(rotation=90)

    def set_rt_and_state_lines(self, port):
        # RT LINE

        self.rt_now[port] = None

        self.rt_array[port] = dict()
        self.rt_xy[port] = dict()
        # Hits
        self.rt_array[port]['hit'] = np.empty([600])
        self.rt_array[port]['hit'][:] = np.nan

        self.rt_xy[port]['hit'] = self.plt[0].\
            plot(self.time_array, self.rt_array[port]['hit'], marker="o")

        c = self.rt_xy[port]['hit'][0].get_color()
        # ---- Misses
        self.rt_array[port]['miss'] = np.empty([600])
        self.rt_array[port]['miss'][:] = np.nan

        self.rt_xy[port]['miss'] = self.plt[0].\
            plot(self.time_array, self.rt_array[port]['miss'], marker="x", color=c)

        # ---- X axes - RT
        self.plt[0].set_xticks([-60, -50, -40, -30, -20, -10, 0])
        self.plt[0].set_xlim([-62, 2])
        self.plt[0].set_yticks(np.arange(0, 2, 1))
        self.plt[0].set_ylim([-0.2, 1.2])


        # STATE LINE
        self.state_now[port] = 0
        self.state_array[port] = np.empty([600])
        self.state_array[port][:] = np.nan

        self.state_xy[port] = self.plt[1].plot(self.time_array, self.state_array[port], marker="")

        # ---- X axes - State
        self.plt[1].set_xticks([-60, -50, -40, -30, -20, -10, 0])
        self.plt[1].set_xlim([-62, 2])

        # RUN ANIMATION
        if self.ani is None:
            self.ani = animation.FuncAnimation(self.fig,
                                                     self._animate,
                                                     init_func=lambda prt=port: self._init_animation(prt),
                                                     interval=10, blit=True)

        self.ports.update([port])

    def _init_animation(self, p):
        self.state_xy[p][0].set_data(self.time_array, self.state_array[p])
        self.rt_xy[p]['hit'][0].set_data(self.time_array, self.rt_array[p]['hit'])
        self.rt_xy[p]['miss'][0].set_data(self.time_array, self.rt_array[p]['miss'])

        self.plot_lines.update(self.state_xy[p])
        self.plot_lines.update(self.rt_xy[p]['hit'])
        self.plot_lines.update(self.rt_xy[p]['miss'])

        return self.plot_lines

    def _animate(self, i):
        if self.run:
            if self.ready_to_update():
                for port in self.ports:
                    try:

                        self.rescale_rt_y(self.rt_now[port])

                        # Hits
                        self.rt_array[port]['hit'] = np.roll(self.rt_array[port]['hit'], -1)
                        self.rt_array[port]['miss'] = np.roll(self.rt_array[port]['miss'], -1)

                        if self.rt_now[port]:
                            if self.rt_now[port] > 0:
                                self.rt_array[port]['hit'][-1] = self.rt_now[port]
                                self.rt_array[port]['miss'][-1] = None
                            else:
                                self.rt_array[port]['miss'][-1] = None
                                self.rt_array[port]['miss'][-1] = self.rt_now[port]
                        else:
                            self.rt_array[port]['hit'][-1] = None
                            self.rt_array[port]['miss'][-1] = None

                        self.rt_xy[port]['hit'][0].set_data(self.time_array, self.rt_array[port]['hit'])
                        self.rt_xy[port]['miss'][0].set_data(self.time_array, self.rt_array[port]['miss'])

                        self.rt_now[port] = None

                        self.plot_lines.update(self.rt_xy[port]['hit'])
                        self.plot_lines.update(self.rt_xy[port]['miss'])

                        self.state_array[port] = np.roll(self.state_array[port], -1)
                        self.state_array[port][-1] = self.state_now[port]
                        self.state_xy[port][0].set_data(self.time_array, self.state_array[port])

                        self.plot_lines.update(self.state_xy[port])
                    except KeyError:
                        pass

        return self.plot_lines

    def ready_to_update(self):
        t = time.time()
        if t >= self.next_update:
            if (t - self.next_update) > .25:
                self.next_update = t
            else:
                self.next_update += self.interval
            return True
        else:
            return False

    def rt_update(self, port=None, val=None):
        if port:
            self.rt_now[port] = val / 1000
        else:
            for port in self.ports:
                self.rt_now[port] = None

    def state_update(self, port, val):
        self.state_now[port] = val

    def rescale_rt_y(self, val=0):
        if val is not None:
            if val >= self.rt_y_max:
                self.plt[0].set_yticks(np.arange(0, val, 1))
                self.plt[0].set_ylim(self.rt_y_min-.3, val * 1.2)
                self.rt_y_max = val
                self.plt[0].figure.canvas.draw_idle()

    # Plot Controls
    def clear_all(self):
        for port in self.state_array.keys():

            self.state_array[port][:] = np.nan
            self.state_xy[port][0].set_data(self.time_array, self.state_array[port])

        for port in self.rt_array.keys():
            self.rt_array[port]['hit'][:] = np.nan
            self.rt_array[port]['miss'][:] = np.nan
            self.rt_xy[port]['hit'][0].set_data(self.time_array, self.rt_array[port]['hit'])
            self.rt_xy[port]['miss'][0].set_data(self.time_array, self.rt_array[port]['miss'])

        self.plt[0].figure.canvas.draw_idle()

    def remove_port(self, port):
        self.state_array.pop(port)
        self.state_xy.pop(port)
        self.rt_array.pop(port)
        self.ports.remove(port)

    def hide_lines(self, port, name=None):
        if name == 'rt':
            self.rt_xy[port]['hit'][0].set_visible(False)
            self.rt_xy[port]['miss'][0].set_visible(False)
        elif name == 'stim_state':
            self.state_xy[port][0].set_visible(False)

    def show_lines(self, port, name=None):
        if name == 'rt':
            self.rt_xy[port]['hit'][0].set_visible(True)
            self.rt_xy[port]['miss'][0].set_visible(True)
        elif name == 'stim_state':
            self.state_xy[port][0].set_visible(True)


