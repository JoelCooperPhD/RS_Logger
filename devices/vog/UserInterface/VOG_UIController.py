from queue import SimpleQueue
from tkinter import Tk

import numpy as np

from devices.vog.UserInterface import VOG_UIView, VOG_UIConfig


class VOGUIController:
    def __init__(self, win, q_out, q_in):
        self._win: Tk = win
        self._q_out: SimpleQueue = q_out
        self._q_in: SimpleQueue = q_in

        self.devices = dict()

        # Experiment
        self._running = False

        # View
        self._UIView = VOG_UIView.VOGTabbedControls(self._win)

        self._UIView.register_configure_clicked_cb(self._configure_button_cb)
        self._UIView.register_stimulus_on_cb(self._stimulus_on_cb)
        self._UIView.register_stimulus_off_cb(self._stimulus_off_cb)

        # Configure Window
        self._cnf_win = VOG_UIConfig.VOGConfigWin(self._q_out)

        self._queue_monitor()

    def _queue_monitor(self):
        while not self._q_in.empty():
            msg = self._q_in.get()
            address, key, val = msg.split('>')

            # Main Controller Events
            if key == 'init':
                self._log_init()
            elif key == 'close':
                self._log_close()
            elif key == 'start':
                self._data_start()
            elif key == 'stop':
                self._data_stop()

            # Tab Events
            elif key == 'devices':
                self._update_devices(val)

            # Messages from vog hardware
            elif key in ['deviceVer', 'configName', 'configMaxOpen',  'configMaxClose',
                         'configDebounce', 'configClickMode', 'buttonControl', 'configButtonControl']:
                self._cnf_win.update_fields(key, val)

            elif key == 'stm':
                self._update_stimulus_plot(val)

            elif key == 'data':
                self._update_tsot_plot(val)

            # Plot Commands
            elif key == 'clear':
                self._clear_plot()

            # File Path
            elif key == 'fpath':
                pass

        self._win.after(10, self._queue_monitor)

    # Main Controller Events
    def _log_init(self, time_stamp=None):
        self._running = True
        for d in self.devices:
            self.devices[d]['stm_on'].configure(state='disabled')
            self.devices[d]['stm_off'].configure(state='disabled')
            self.devices[d]['configure'].configure(state='disabled')
            self.devices[self._UIView.NB.tab(self._UIView.NB.select(), "text")]['plot'].clear_all()

            self.devices[d]['plot'].run = True
            self.devices[d]['plot'].clear_all()
            self._reset_results_text()

    def _log_close(self, time_stamp=None):
        self._running = False
        for d in self.devices:
            self.devices[d]['stm_on'].configure(state='normal')
            self.devices[d]['stm_off'].configure(state='normal')
            self.devices[d]['configure'].configure(state='normal')
            self.devices[d]['plot'].run = False

    def _data_start(self, time_stamp=None):
        for d in self.devices:
            self.devices[d]['plot'].recording = True
        port = self._UIView.NB.tab(self._UIView.NB.select(), "text")
        self.devices[port]['plot'].state_update(port, np.nan)

    def _data_stop(self, time_stamp=None):
        port = self._UIView.NB.tab(self._UIView.NB.select(), "text")
        self.devices[port]['plot'].state_update(port, np.nan)
        for d in self.devices:
            self.devices[d]['plot'].recording = False

    # Tab Events
    def _update_devices(self, devices=None):
        units = list()
        if devices:
            units = devices.split(",")
            self._UIView.show()
        else:
            self._UIView.hide()

        to_add = set(units) - set(self.devices)
        if to_add:
            for id_ in to_add:
                if id_ not in self.devices:
                    self.devices[id_] = self._UIView.build_tab(id_)
                    self._q_out.put(f'main>stop>ALL')
                    pass

        to_remove = set(self.devices) - set(units)
        if to_remove:
            for id_ in to_remove:
                if id_ in self.devices.keys():
                    self.devices.pop(id_)
                    self._UIView.NB.forget(self._UIView.NB.children[id_.lower()])

    # Messages from vog hardware
    def _update_stimulus_plot(self, state):
        port = self._UIView.NB.tab(self._UIView.NB.select(), "text")
        if self._running:
            self.devices[port]['plot'].state_update(port, state)

    def _update_tsot_plot(self, arg):
        port = self._UIView.NB.tab(self._UIView.NB.select(), "text")
        if self._running:
            trial, opened, closed = arg.split(',')
            opened = int(opened)
            closed = int(closed)

            self.devices[port]['trl_n'].set(trial)
            self.devices[port]['tsot'].set(opened)
            self.devices[port]['tsct'].set(closed)

            self.devices[port]['plot'].tsot_update(port, opened)

            self.devices[port]['plot'].tsct_update(port, closed)

    def _reset_results_text(self):
        for d in self.devices:
            self._update_trial_text(d, '0')
            self._update_tsot_text(d, '0')
            self._update_tsct_text(d, '0')

    def _update_trial_text(self, unit_id, cnt):
        if self._running:
            self.devices[unit_id]['trl_n'].set(cnt)

    def _update_tsot_text(self, unit_id, tsot):
        if self._running:
            self.devices[unit_id]['tsot'].set(tsot)

    def _update_tsct_text(self, unit_id, tsct):
        if self._running:
            self.devices[unit_id]['tsct'].set(tsct)

    # Plot Commands
    def _clear_plot(self):
        for d in self.devices:
            self.devices[d]['plot'].clear_all()

    def _stop_plotter(self):
        for d in self.devices:
            self.devices[d]['plot'].run = False

    def _stimulus_on_cb(self):
        com = self._UIView.NB.tab(self._UIView.NB.select(), 'text')
        self._q_out.put(f"hi_vog>do_peekOpen>{com}")

    def _stimulus_off_cb(self):
        com = self._UIView.NB.tab(self._UIView.NB.select(), 'text')
        self._q_out.put(f"hi_vog>do_peekClose>{com}")

    def _configure_button_cb(self):
        self._cnf_win.show(self._UIView.NB.tab(self._UIView.NB.select(), "text"))
        self._q_out.put(f"hi_vog>get_config>{self._UIView.NB.tab(self._UIView.NB.select(), 'text')}")

