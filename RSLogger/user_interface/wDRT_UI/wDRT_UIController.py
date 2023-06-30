from queue import SimpleQueue
from tkinter import Tk, TclError

import numpy as np

from RSLogger.user_interface.wDRT_UI import wDRT_UIView, wDRT_UIConfig


class WDRTUIController:
    def __init__(self, win, q_out, debug=False):
        self._debug = debug

        self._win: Tk = win
        self._q_2_hi: SimpleQueue = q_out

        self.devices = dict()

        # Experiment
        self._running = False

        # wDRT_UI
        self._view = wDRT_UIView.WDRTMainWindow(win)
        self._view.NB.bind("<<NotebookTabChanged>>", self._tab_changed_cb)
        self._view.register_stim_on_cb(self._stim_on_button_cb)
        self._view.register_stim_off_cb(self._stim_off_button_cb)
        self._view.register_configure_clicked_cb(self._configure_button_cb)
        self._view.register_rescan_network(self._rescan_network_cb)
        self._active_tab = None

        # Configure Window
        self._cnf_win = wDRT_UIConfig.WDRTConfigWin()
        self._cnf_win.register_custom_cb(self._custom_button_cb)
        self._cnf_win.register_iso_cb(self._iso_button_cb)

    def handle_command(self, com, key, val):
        # Tab Events
        if key == 'devices':
            self._update_devices(val)
        elif key == 'remove' : self._remove_tab(val)

        # Plot Commands
        elif key == 'clear'  : self._clear_plot()

        # Messages from DRT unit
        elif key == 'cfg'    : self._update_configuration(val)
        elif key == 'stm'    :
            self._update_stim_state(val, com)
        elif key == 'dta'    : self._update_stim_data(val, com)
        elif key == 'bty'    : self._update_battery_soc(val, com)
        elif key == 'trl'    : self._update_trial_number(val, com)
        elif key == 'rt'     : self._update_rt(val, com)
        elif key == 'clk'    : self._update_clicks(val, com)

        elif key == 'fpath'  : self._update_file_path(val)

    def handle_control_command(self, key, val):
        if   key == 'init'    : self._log_init(val)
        elif key == 'close'   : self._log_close(val)
        elif key == 'start'   : self._data_record(val)
        elif key == 'stop'    : self._data_pause(val)

    def _update_devices(self, devices=None):
        units = list()
        if devices:
            units = devices.split(",")
            self._view.show()
        else:
            self._view.hide()

        to_add = set(units) - set(self.devices)
        if to_add:
            for id_ in to_add:
                if id_ not in self.devices:
                    self.devices[id_] = self._view.build_tab(id_)
                    self._q_2_hi.put(f'wDRT>{id_}>stop>')

        to_remove = set(self.devices) - set(units)
        if to_remove:
            for id_ in to_remove:
                if id_ in self.devices.keys():
                    self.devices.pop(id_)
                    self._view.NB.forget(self._view.NB.children[id_.lower()])

    def _add_tab(self, dev_ids):
        for id_ in dev_ids:
            if id_ not in self.devices:
                self.devices[id_] = self._view.build_tab(id_)

    def _remove_tab(self, dev_ids):
        for id_ in dev_ids:
            if id_ in self.devices.keys():
                self.devices.pop(id_)
                self._view.NB.forget(self._view.NB.children[id_.lower()])

    # sDRT_UI Parent
    def _log_init(self, arg):
        for unit_id in self.devices:
            self.devices[unit_id]['rt'].set(-1)
            self.devices[unit_id]['trl_n'].set(0)
            self.devices[unit_id]['clicks'].set(0)

            self.devices[unit_id]['plot'].run = True
            self.devices[unit_id]['plot'].clear_all()
            self.devices[unit_id]['plot'].state_update(unit_id, -1)

    def _log_close(self, arg):
        for unit_id in self.devices:
            self.devices[unit_id]['plot'].run = False
            self.devices[unit_id]['plot'].state_update(unit_id, -1)

    def _data_record(self, arg):
        self._running = True
        for unit_id in self.devices:
            self.devices[unit_id]['plot'].state_update(unit_id, 0)

    def _data_pause(self, arg):
        self._running = False
        for unit_id in self.devices:
            self.devices[unit_id]['plot'].state_update(unit_id, np.nan)

    def _update_file_path(self, arg):
        pass

    # Registered Callbacks with wDRT sDRT_UI
    def _tab_changed_cb(self, e):
        try:
            self._active_tab = self._view.NB.tab(self._view.NB.select(), "text")
            if self.devices:
                self._q_2_hi.put(f"wDRT>{self._active_tab}>get_bat>")
        except TclError as e:
            if self._debug: print(e)

    def _stim_on_button_cb(self):
        self._q_2_hi.put(f"wDRT>{self._active_tab}>stm_on>")

    def _stim_off_button_cb(self):
        self._q_2_hi.put(f"wDRT>{self._active_tab}>stm_off>")

    def _configure_button_cb(self):
        self._cnf_win.show(self._active_tab)
        self._q_2_hi.put(f"wDRT>{self._active_tab}>get_cfg>")

    def _rescan_network_cb(self):
        for c in self._view.NB.winfo_children():
            try:
                self._view.NB.forget(c)
            except TclError:
                pass
        self.devices.clear()
        self._q_2_hi.put(f"wDRT>{self._active_tab}>net_scn>")
        self._view.hide()

    # Plotter
    def _update_stim_state(self, arg, com):
        if self._running:
            self.devices[com]['plot'].state_update(com, arg)

    def _update_stim_data(self, arg, unit_id):
        if self._running:
            block_ms, trial_n, clicks, rt, bty, device_utc = arg.strip().split(',')
            if rt == "-1":
                self.devices[unit_id]['plot'].rt_update(unit_id, -.0001)
            self.devices[unit_id]['rt'].set(-1)
            self.devices[unit_id]['trl_n'].set(trial_n)
            self.devices[unit_id]['clicks'].set(0)
            self._update_battery_soc(bty, unit_id)

    def _update_rt(self, rt, unit_id):
        if self._running:
            if rt != 'None':
                rt = round((int(rt) / 1000000), 2)
                self.devices[unit_id]['rt'].set(rt)
                self.devices[unit_id]['plot'].rt_update(unit_id, rt)

    def _update_trial_number(self, trl_n, unit_id):
        self.devices[unit_id]['trl_n'].set(trl_n)

    def _update_clicks(self, arg, unit_id):
        if self._running:
            self.devices[unit_id]['clicks'].set(arg)

    def _update_battery_soc(self, arg, unit_id=None):
        if 'COM' not in unit_id:
            soc = arg
            if isinstance(arg, list):
                unit_id, soc = arg[0].strip().split(',')

            p = int(soc) // 10
            for i in range(10):
                color = 'white'
                if p >= i + 1:
                    color = 'black' if p > 2 else 'red'
                try:
                    self.devices[unit_id][f'b_{i}'].config(bg=color)
                except Exception as e:
                    print(e)

    def _stop_plotter(self):
        self.devices[self._active_tab]['plot'].run = False

    def _clear_plot(self):
        self.devices[self._active_tab]['plot'].clear_all()

    # Configuration Window
    # ---- Registered Callbacks
    def _custom_button_cb(self, msg):
        self._q_2_hi.put(f"wDRT>{self._active_tab}>set>{msg}")

    def _iso_button_cb(self):
        self._q_2_hi.put(f"wDRT>{self._active_tab}>iso>")

    # ---- msg from wDRT unit
    def _update_configuration(self, args):
        self._cnf_win.parse_config(args)
