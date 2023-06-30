from queue import SimpleQueue
from tkinter import Tk, TclError
from RSLogger.user_interface.wVOG_UI import wVOG_UIView, wVOG_UIConfig
from numpy import nan
from time import time_ns


class WVOGUIController:
    def __init__(self, win, q_out, debug=False):
        self._debug = debug
        if self._debug: print(f'{time_ns()} WVOGUIController.__init__')

        self._win: Tk = win
        self._q_2_hi: SimpleQueue = q_out

        self.devices = dict()

        # Experiment
        self._running = False

        # wVOG_UI
        self._view = wVOG_UIView.wVOGTabbedControls(win)
        self._view.NB.bind("<<NotebookTabChanged>>", self._tab_changed_cb)

        self._view.register_stimulus_a_toggle_cb(self._stimulus_a_toggle_cb)
        self._view.register_stimulus_b_toggle_cb(self._stimulus_b_toggle_cb)
        self._view.register_stimulus_ab_toggle_cb(self._stimulus_ab_toggle_cb)

        self._view.register_configure_clicked_cb(self._configure_button_cb)
        self._active_tab = None

        self._view.register_rescan_network(self._rescan_network_cb)

        # Configure Window
        self._cnf_win = wVOG_UIConfig.VOGConfigWin(self._q_2_hi)

    def handle_command(self, com, key, val):
        if self._debug: print(f'{time_ns()} WVOGUIController.handle_command')

        # Tab Events
        if key == 'devices':
            self._update_devices(val)
        elif key == 'remove' : self._remove_tab(val)

        # Plot Commands
        elif key == 'clear'  : self._clear_plot()

        # Messages from wVOG unit
        elif key == 'cfg'    : self._update_configuration(val)

        elif key in ['a', 'b', 'x']:
            self._update_stim_state(val, com)

        elif key == 'dta'    : self._update_tsot_tsct_data(val, com)
        elif key == 'bty'    : self._update_battery_soc(val, com)
        elif key == 'fpath'  : self._update_file_path(val)

        elif key == 'stm'    : self._update_stim_state(val, com)

    def handle_control_command(self, key, val):
        if self._debug: print(f'{time_ns()} WVOGUIController.handle_control_command')

        if   key == 'init'    : self._log_init(val)
        elif key == 'close'   : self._log_close(val)
        elif key == 'start'   : self._data_record(val)
        elif key == 'stop'    : self._data_pause(val)

    def _update_devices(self, devices=None):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_devices')

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

        to_remove = set(self.devices) - set(units)
        if to_remove:
            for id_ in to_remove:
                if id_ in self.devices.keys():
                    self.devices.pop(id_)
                    self._view.NB.forget(self._view.NB.children[id_.lower()])

    def _add_tab(self, dev_ids):
        if self._debug: print(f'{time_ns()} WVOGUIController._add_tab')

        for id_ in dev_ids:
            if id_ not in self.devices:
                self.devices[id_] = self._view.build_tab(id_)

    def _remove_tab(self, dev_ids):
        if self._debug: print(f'{time_ns()} WVOGUIController._remove_tab')

        for id_ in dev_ids:
            if id_ in self.devices.keys():
                self.devices.pop(id_)
                self._view.NB.forget(self._view.NB.children[id_.lower()])

    # wVOG_UI Parent
    def _log_init(self, arg):
        if self._debug: print(f'{time_ns()} WVOGUIController._log_init')

        self._toggle_state('disabled')
        self._running = True
        for d in self.devices:
            self.devices[self._view.NB.tab(self._view.NB.select(), "text")]['plot'].clear_all()
            self.devices[d]['plot'].run = True
            self.devices[d]['plot'].clear_all()
            self.devices[d]['plot'].run = True
            self._reset_results_text()

    def _log_close(self, arg):
        if self._debug: print(f'{time_ns()} WVOGUIController._log_close')

        self._running = False
        self._toggle_state('normal')
        for d in self.devices:
            self.devices[d]['plot'].run = False

    def _data_record(self, arg):
        if self._debug: print(f'{time_ns()} WVOGUIController._data_record')

        for d in self.devices:
            self.devices[d]['plot'].recording = True

    def _data_pause(self, arg):
        if self._debug: print(f'{time_ns()} WVOGUIController._data_pause')

        for d in self.devices:
            self.devices[d]['plot'].state_update(d, nan)
            self.devices[d]['plot'].recording = False

    def _toggle_state(self, state):
        if self._debug: print(f'{time_ns()} WVOGUIController. _toggle_state')

        for d in self.devices:

            self.devices[d]['a_toggle'].configure(state=state)
            self.devices[d]['b_toggle'].configure(state=state)
            self.devices[d]['ab_toggle'].configure(state=state)
            self.devices[d]['configure'].configure(state=state)
            try:
                self.devices[d]['refresh'].config(state=state)
            except KeyError:
                pass

    def _update_file_path(self, arg):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_file_path')
        pass

    # Registered Callbacks with wVOG UI
    def _tab_changed_cb(self, e):
        if self._debug: print(f'{time_ns()} WVOGUIController._tab_changed_cb')

        if self.devices:
            try:
                # Clean up old tab and device
                if self._running:
                    self.devices[self._active_tab]['plot'].run = False
                    self.devices[self._active_tab]['plot'].clear_all()

                # Start new tab and device
                self._active_tab = self._view.NB.tab(self._view.NB.select(), "text")
                if 'COM' not in self._active_tab:
                    self._q_2_hi.put(f"wVOG>{self._active_tab}>get_bat>")
                if self._running:
                    self.devices[self._active_tab]['plot'].run = True
                    self.devices[self._active_tab]['plot'].clear_all()
            except Exception as e:
                pass

    def _lens_change_cb(self, lens, state):
        if self._debug: print(f'{time_ns()} WVOGUIController._lens_change_cb')

        self._q_2_hi.put(f"wVOG>{self._active_tab}>{lens}_{state}>")

    def _configure_button_cb(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._configure_button_cb')

        self._cnf_win.show(self._active_tab)
        self._q_2_hi.put(f"wVOG>{self._active_tab}>get_cfg>")

    def _rescan_network_cb(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._rescan_network_cb')

        for c in self._view.NB.winfo_children():
            try:
                self._view.NB.forget(c)
            except TclError:
                pass
        self.devices.clear()
        self._q_2_hi.put(f"wVOG>{self._active_tab}>net_scn>")
        self._view.hide()

    # Messages from vog hardware
    def _update_tsot_plot(self, arg):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_tsot_plot')

        if self._running:
            port = self._view.NB.tab(self._view.NB.select(), "text")
            device = self.devices[port]

            trial, opened, closed = map(int, arg.split(','))

            device['trl_n'].set(trial)
            device['tsot'].set(opened)
            device['tsct'].set(closed)

            device['plot'].tsot_update(port, opened)
            device['plot'].tsct_update(port, closed)

    def _reset_results_text(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._reset_results_text')

        for d in self.devices:
            self._update_trial_text(d, '0')
            self._update_tsot_text(d, '0')
            self._update_tsct_text(d, '0')

    def _update_trial_text(self, unit_id, cnt):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_trial_text')

        if self._running:
            self.devices[unit_id]['trl_n'].set(cnt)

    def _update_tsot_text(self, unit_id, tsot):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_tsot_text')

        if self._running:
            self.devices[unit_id]['tsot'].set(tsot)

    def _update_tsct_text(self, unit_id, tsct):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_tsct_text')

        if self._running:
            self.devices[unit_id]['tsct'].set(tsct)

        # Plot Commands

    def _clear_plot(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._clear_plot')

        for d in self.devices:
            self.devices[d]['plot'].clear_all()

    def _stop_plotter(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._stop_plotter')

        for d in self.devices:
            self.devices[d]['plot'].run = False

    def _stimulus_a_toggle_cb(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._stimulus_a_toggle_cb')

        com = self._view.NB.tab(self._view.NB.select(), 'text')
        if self.devices[com]['a_toggle']['text'] == 'A Open':
            self.devices[com]['a_toggle']['text'] = 'A Close'
            self._q_2_hi.put(f"wVOG>{com}>stm_a>1")
        else:
            self.devices[com]['a_toggle']['text'] = 'A Open'
            self._q_2_hi.put(f"wVOG>{com}>stm_a>0")

    def _stimulus_b_toggle_cb(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._stimulus_b_toggle_cb')

        com = self._view.NB.tab(self._view.NB.select(), 'text')
        if self.devices[com]['b_toggle']['text'] == 'B Open':
            self.devices[com]['b_toggle']['text'] = 'B Close'
            self._q_2_hi.put(f"wVOG>{com}>stm_b>1")
        else:
            self.devices[com]['b_toggle']['text'] = 'B Open'
            self._q_2_hi.put(f"wVOG>{com}>stm_b>0")

    def _stimulus_ab_toggle_cb(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._stimulus_ab_toggle_cb')

        com = self._view.NB.tab(self._view.NB.select(), 'text')
        if self.devices[com]['ab_toggle']['text'] == 'AB Open':
            self.devices[com]['ab_toggle']['text'] = 'AB Close'
            self._q_2_hi.put(f"wVOG>{com}>stm_x>1")
        else:
            self.devices[com]['ab_toggle']['text'] = 'AB Open'
            self._q_2_hi.put(f"wVOG>{com}>stm_x>0")

    # Plotter
    def _update_stim_state(self, arg, unit_id):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_stim_state')

        if self._running and unit_id in self.devices:
            self.devices[unit_id]['plot'].state_update(unit_id, arg)

    def _update_tsot_tsct_data(self, arg, unit_id):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_tsot_tsct_data')

        if self._running and unit_id in self.devices:
            trl_n, tsot, tsct, ttt, state, bat, utc = arg.strip().split(',')
            if unit_id == self._active_tab:
                self._update_battery_soc(bat, unit_id)
                self.devices[unit_id]['trl_n'].set(trl_n)
                self.devices[unit_id]['tsot'].set(tsot)
                self.devices[unit_id]['tsct'].set(tsct)
            self.devices[unit_id]['plot'].tsot_update(unit_id, tsot)
            self.devices[unit_id]['plot'].tsct_update(unit_id, tsct)

    def _update_battery_soc(self, arg, unit_id=None):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_battery_soc')

        if 'COM' not in unit_id:
            soc = arg
            if isinstance(arg, list):
                unit_id, soc = arg[0].strip().split(',')

            p = int(soc) // 10
            for i in range(10):
                color = 'white'
                if p >= i + 1:
                    color = 'black' if p > 2 else 'red'
                self.devices[unit_id][f'b_{i}'].config(bg=color)

    # Configuration Window
    # ---- Registered Callbacks
    def _custom_button_cb(self, msg):
        if self._debug: print(f'{time_ns()} WVOGUIController._custom_button_cb')

        self._q_2_hi.put(f"wVOG>{self._active_tab}>set_cfg>{msg}")

    def _nhtsa_button_cb(self):
        if self._debug: print(f'{time_ns()} WVOGUIController._nhtsa_button_cb')

        self._q_2_hi.put(f"wVOG>{self._active_tab}>set_nhtsa>")

    # ---- msg from wVOG unit
    def _update_configuration(self, args):
        if self._debug: print(f'{time_ns()} WVOGUIController._update_configuration')

        self._cnf_win.parse_config(args)
