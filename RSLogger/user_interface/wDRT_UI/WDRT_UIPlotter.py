import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time


class Plotter:
    def __init__(self, frame):
        # Chart
        self._fig = Figure(figsize=(4, 2), dpi=100)
        self._fig.suptitle("Detection Response Task - DRT")
        self._canvas = FigureCanvasTkAgg(self._fig, master=frame)
        self._canvas.get_tk_widget().grid(row=0, column=0, padx=2, pady=2, sticky='NEWS', rowspan=20)

        self._plt = list()

        self._unit_ids = set()

        # Plot time
        self._time_array = np.arange(-60, 0, .1)

        # Plot tic
        self._next_update = time.time()
        self._interval = .1

        # Reaction Time
        self._rt_now = dict()
        self._rt_array = dict()
        self._rt_xy = dict()
        self._plot_lines = set()

        self._rt_y_min = 0
        self._rt_y_max = 2

        # Stimulus State
        self._state_now = dict()
        self._state_array = dict()
        self._state_xy = dict()

        # Animation
        self._ani = None

        self._add_rt_plot()
        self._add_state_plot()

        self.run = False

    def _add_rt_plot(self):
        self._plt.append(self._fig.add_subplot(212))
        # Y axes
        self._plt[0].set_ylabel("RT-Seconds")
        self._plt[0].yaxis.set_label_position('right')
        self._plt[0].yaxis.set_tick_params()

    def _add_state_plot(self):
        self._plt.append(self._fig.add_subplot(211))

        # X axes
        self._plt[1].xaxis.set_tick_params(labelbottom=False)
        # Y axes
        self._plt[1].set_ylabel("Stimulus")
        self._plt[1].yaxis.set_label_position('right')
        self._plt[1].set_ylim([-0.2, 1.2])
        self._plt[1].set_yticks([0, 1])
        self._plt[1].set_yticklabels(["Off", "On"])

    def set_rt_and_state_lines(self, unit_id):
        # RT LINE

        self._rt_now[unit_id] = None

        self._rt_array[unit_id] = dict()
        self._rt_xy[unit_id] = dict()
        # Hits
        self._rt_array[unit_id]['hit'] = np.empty([600])
        self._rt_array[unit_id]['hit'][:] = np.nan

        self._rt_xy[unit_id]['hit'] = self._plt[0].\
            plot(self._time_array, self._rt_array[unit_id]['hit'], marker="o")

        c = self._rt_xy[unit_id]['hit'][0].get_color()
        # ---- Misses
        self._rt_array[unit_id]['miss'] = np.empty([600])
        self._rt_array[unit_id]['miss'][:] = np.nan

        self._rt_xy[unit_id]['miss'] = self._plt[0].\
            plot(self._time_array, self._rt_array[unit_id]['miss'], marker="x", color=c)

        # ---- X axes - RT
        self._plt[0].set_xticks([-60, -50, -40, -30, -20, -10, 0])
        self._plt[0].set_xlim([-62, 2])
        self._plt[0].set_yticks(np.arange(0, 2, 1))
        self._plt[0].set_ylim([-0.2, 1.2])

        # STATE LINE
        self._state_now[unit_id] = 0
        self._state_array[unit_id] = np.empty([600])
        self._state_array[unit_id][:] = np.nan

        self._state_xy[unit_id] = self._plt[1].plot(self._time_array, self._state_array[unit_id], marker="")

        # ---- X axes - State
        self._plt[1].set_xticks([-60, -50, -40, -30, -20, -10, 0])
        self._plt[1].set_xlim([-62, 2])

        # RUN ANIMATION
        if self._ani is None:
            self._ani = animation.FuncAnimation(self._fig,
                                                self._animate,
                                                init_func=lambda prt=unit_id: self._init_animation(prt),
                                                interval=10, blit=True)

        self._unit_ids.update([unit_id])

    def _init_animation(self, p):
        self._state_xy[p][0].set_data(self._time_array, self._state_array[p])
        self._rt_xy[p]['hit'][0].set_data(self._time_array, self._rt_array[p]['hit'])
        self._rt_xy[p]['miss'][0].set_data(self._time_array, self._rt_array[p]['miss'])

        self._plot_lines.update(self._state_xy[p])
        self._plot_lines.update(self._rt_xy[p]['hit'])
        self._plot_lines.update(self._rt_xy[p]['miss'])

        return self._plot_lines

    def _animate(self, i):
        if self.run:
            if self._ready_to_update():

                for unit_id in self._unit_ids:
                    try:
                        self._rescale_rt_y(self._rt_now[unit_id])

                        # Hits
                        self._rt_array[unit_id]['hit'] = np.roll(self._rt_array[unit_id]['hit'], -1)
                        self._rt_array[unit_id]['miss'] = np.roll(self._rt_array[unit_id]['miss'], -1)

                        if self._rt_now[unit_id]:
                            if self._rt_now[unit_id] > 0:
                                self._rt_array[unit_id]['hit'][-1] = self._rt_now[unit_id]
                                self._rt_array[unit_id]['miss'][-1] = None
                            else:
                                self._rt_array[unit_id]['miss'][-1] = None
                                self._rt_array[unit_id]['miss'][-1] = self._rt_now[unit_id]
                        else:
                            self._rt_array[unit_id]['hit'][-1] = None
                            self._rt_array[unit_id]['miss'][-1] = None

                        self._rt_xy[unit_id]['hit'][0].set_data(self._time_array, self._rt_array[unit_id]['hit'])
                        self._rt_xy[unit_id]['miss'][0].set_data(self._time_array, self._rt_array[unit_id]['miss'])

                        self._rt_now[unit_id] = None

                        self._plot_lines.update(self._rt_xy[unit_id]['hit'])
                        self._plot_lines.update(self._rt_xy[unit_id]['miss'])

                        self._state_array[unit_id] = np.roll(self._state_array[unit_id], -1)
                        self._state_array[unit_id][-1] = self._state_now[unit_id]
                        self._state_xy[unit_id][0].set_data(self._time_array, self._state_array[unit_id])

                        self._plot_lines.update(self._state_xy[unit_id])
                    except KeyError:
                        pass

        return self._plot_lines

    def _ready_to_update(self):
        t = time.time()
        if t >= self._next_update:
            if (t - self._next_update) > .25:
                self._next_update = t
            else:
                self._next_update += self._interval
            return True
        else:
            return False

    def _rescale_rt_y(self, val=0):
        if val is not None:
            if val >= self._rt_y_max:
                self._plt[0].set_yticks(np.arange(0, val, 1))
                self._plt[0].set_ylim(self._rt_y_min - .3, val * 1.2)
                self._rt_y_max = val
                self._plt[0].figure.canvas.draw_idle()

    # Plot Controls
    def rt_update(self, unit_id, val):
        self._rt_now[unit_id] = val

    def state_update(self, unit_id, val):
        self._state_now[unit_id] = val

    def clear_all(self):
        for unit_id in self._state_array.keys():
            self._state_now[unit_id] = 0
            self._state_array[unit_id][:] = np.nan
            self._state_xy[unit_id][0].set_data(self._time_array, self._state_array[unit_id])

        for unit_id in self._rt_array.keys():
            self._rt_array[unit_id]['hit'][:] = np.nan
            self._rt_array[unit_id]['miss'][:] = np.nan
            self._rt_xy[unit_id]['hit'][0].set_data(self._time_array, self._rt_array[unit_id]['hit'])
            self._rt_xy[unit_id]['miss'][0].set_data(self._time_array, self._rt_array[unit_id]['miss'])

        self._plt[0].figure.canvas.draw_idle()

    def remove_unit_id(self, unit_id):
        self._state_array.pop(unit_id)
        self._state_xy.pop(unit_id)
        self._rt_array.pop(unit_id)
        self._unit_ids.remove(unit_id)

    def hide_lines(self, unit_id, name=None):
        if name == 'rt':
            self._rt_xy[unit_id]['hit'][0].set_visible(False)
            self._rt_xy[unit_id]['miss'][0].set_visible(False)
        elif name == 'stim_state':
            self._state_xy[unit_id][0].set_visible(False)

    def show_lines(self, unit_id, name=None):
        if name == 'rt':
            self._rt_xy[unit_id]['hit'][0].set_visible(True)
            self._rt_xy[unit_id]['miss'][0].set_visible(True)
        elif name == 'stim_state':
            self._state_xy[unit_id][0].set_visible(True)


