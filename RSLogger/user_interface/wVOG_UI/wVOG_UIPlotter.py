import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import time


class Plotter:
    def __init__(self, frame):
        # Chart
        self._fig = Figure(figsize=(4, 2), dpi=100)
        self._fig.suptitle("wVOG - Wireless Visual Occlusion Goggles")
        self._canvas = FigureCanvasTkAgg(self._fig, master=frame)
        self._canvas.get_tk_widget().grid(row=0, column=0, padx=2, pady=2, sticky='NEWS', rowspan=20)

        self._plt = list()

        self._unit_ids = set()

        # Plot time
        self._time_array = np.arange(-60, 0, .1)

        # Plot tic
        self._next_update = time.time()
        self._interval = .1

        # Total Shutter Times
        self._tsot_now = dict()
        self._tsct_now = dict()

        self._tst_array = dict()
        self._tst_xy = dict()

        self._tst_y_min = 0
        self._tst_y_max = 1

        self._plot_lines = set()

        # Stimulus State
        self._state_now = dict()
        self._state_array = dict()
        self._state_xy = dict()

        # Animation
        self._ani = None

        self._add_tsot_plot()
        self._add_state_plot()

        self.run = False

        self.recording = False

    def _add_tsot_plot(self):
        self._plt.append(self._fig.add_subplot(212))
        # Y axes
        self._plt[0].set_ylabel("TSOT-TSCT")
        self._plt[0].yaxis.set_label_position('right')
        self._plt[0].yaxis.set_tick_params()

    def _add_state_plot(self):
        self._plt.append(self._fig.add_subplot(211))

        # X axes
        self._plt[1].xaxis.set_tick_params(labelbottom=False)
        # Y axes
        self._plt[1].set_ylabel("State")
        self._plt[1].yaxis.set_label_position('right')
        self._plt[1].set_ylim([-0.2, 1.2])
        self._plt[1].set_yticks([0, 1])
        self._plt[1].set_yticklabels(["Opaque", "Clear"])


    def set_tsot_and_state_lines(self, unit_id):
        # RT LINE

        self._tsot_now[unit_id] = None
        self._tsct_now[unit_id] = None

        self._tst_array[unit_id] = dict()
        self._tst_xy[unit_id] = dict()

        # TSOT
        self._tst_array[unit_id]['tsot'] = np.empty([600])
        self._tst_array[unit_id]['tsot'][:] = np.nan

        self._tst_xy[unit_id]['tsot'] = self._plt[0].\
            plot(self._time_array, self._tst_array[unit_id]['tsot'], marker="o")

        c = self._tst_xy[unit_id]['tsot'][0].get_color()

        # TSCT
        self._tst_array[unit_id]['tsct'] = np.empty([600])
        self._tst_array[unit_id]['tsct'][:] = np.nan

        self._tst_xy[unit_id]['tsct'] = self._plt[0].\
            plot(self._time_array, self._tst_array[unit_id]['tsct'], marker="_", color=c)

        # ---- X axes - TST
        self._plt[0].set_xticks([-60, -50, -40, -30, -20, -10, 0])
        self._plt[0].set_xlim([-62, 2])
        self._plt[0].set_yticks(np.arange(0, 3000, 1000))
        self._plt[0].set_ylim([0, 3000])

        # STATE LINE
        self._state_now[unit_id] = np.nan
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
                                                interval=10, blit=True, cache_frame_data=False)

        self._unit_ids.update([unit_id])

    def _init_animation(self, p):
        self._state_xy[p][0].set_data(self._time_array, self._state_array[p])
        self._tst_xy[p]['tsot'][0].set_data(self._time_array, self._tst_array[p]['tsot'])
        self._tst_xy[p]['tsct'][0].set_data(self._time_array, self._tst_array[p]['tsct'])

        self._plot_lines.update(self._state_xy[p])
        self._plot_lines.update(self._tst_xy[p]['tsot'])
        self._plot_lines.update(self._tst_xy[p]['tsct'])

        return self._plot_lines

    def _animate(self, i):
        if self.run:
            if self._ready_to_update():

                for unit_id in self._unit_ids:

                    self._rescale_y(self._tsot_now[unit_id], self._tsct_now[unit_id])

                    # TST
                    self._tst_array[unit_id]['tsot'] = np.roll(self._tst_array[unit_id]['tsot'], -1)
                    self._tst_array[unit_id]['tsct'] = np.roll(self._tst_array[unit_id]['tsct'], -1)

                    if self._tsot_now[unit_id]:
                        self._tst_array[unit_id]['tsot'][-1] = self._tsot_now[unit_id]

                    if self._tsct_now[unit_id]:
                        self._tst_array[unit_id]['tsct'][-1] = self._tsct_now[unit_id]

                    self._tst_xy[unit_id]['tsot'][0].set_data(self._time_array, self._tst_array[unit_id]['tsot'])
                    self._tst_xy[unit_id]['tsct'][0].set_data(self._time_array, self._tst_array[unit_id]['tsct'])

                    self._tsot_now[unit_id] = np.nan
                    self._tsct_now[unit_id] = np.nan

                    self._plot_lines.update(self._tst_xy[unit_id]['tsot'])
                    self._plot_lines.update(self._tst_xy[unit_id]['tsct'])

                    # State
                    self._state_array[unit_id] = np.roll(self._state_array[unit_id], -1)
                    self._state_array[unit_id][-1] = self._state_now[unit_id]

                    self._state_xy[unit_id][0].set_data(self._time_array, self._state_array[unit_id])

                    self._plot_lines.update(self._state_xy[unit_id])

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

    def _rescale_y(self, tsot, tsct):
        try:
            if tsot and tsct:
                val = max(tsot, tsct)
                if val is not None:
                    if val >= self._tst_y_max:
                        val = round(val/1000) * 1000
                        tic_width = round(val/3/1000)*1000
                        self._plt[0].set_yticks(np.arange(0, val*1.2, tic_width))
                        self._plt[0].set_ylim(self._tst_y_min - .3, val * 1.2)
                        self._tst_y_max = val
                        self._plt[0].figure.canvas.draw_idle()
        except ZeroDivisionError:
            pass

    # Plot Controls
    def tsot_update(self, unit_id, val):
        self._tsot_now[unit_id] = int(val)

    def tsct_update(self, unit_id, val):
        self._tsct_now[unit_id] = int(val)

    def state_update(self, unit_id, val):
        if self.recording:
            self._state_now[unit_id] = val

    def clear_all(self):
        for unit_id in self._state_array.keys():
            self._state_now[unit_id] = np.nan
            self._state_array[unit_id][:] = np.nan
            self._state_xy[unit_id][0].set_data(self._time_array, self._state_array[unit_id])

        for unit_id in self._tst_array.keys():
            self._tst_array[unit_id]['tsot'][:] = np.nan
            self._tst_array[unit_id]['tsct'][:] = np.nan
            self._tst_xy[unit_id]['tsot'][0].set_data(self._time_array, self._tst_array[unit_id]['tsot'])
            self._tst_xy[unit_id]['tsct'][0].set_data(self._time_array, self._tst_array[unit_id]['tsct'])

        self._plt[0].figure.canvas.draw_idle()

    def remove_unit_id(self, unit_id):
        self._state_array.pop(unit_id)
        self._state_xy.pop(unit_id)
        self._tst_array.pop(unit_id)
        self._unit_ids.remove(unit_id)

    def hide_lines(self, unit_id, name=None):
        if name == 'rt':
            self._tst_xy[unit_id]['tsot'][0].set_visible(False)
            self._tst_xy[unit_id]['tsct'][0].set_visible(False)
        elif name == 'stim_state':
            self._state_xy[unit_id][0].set_visible(False)

    def show_lines(self, unit_id, name=None):
        if name == 'rt':
            self._tst_xy[unit_id]['tsot'][0].set_visible(True)
            self._tst_xy[unit_id]['tsct'][0].set_visible(True)
        elif name == 'stim_state':
            self._state_xy[unit_id][0].set_visible(True)


