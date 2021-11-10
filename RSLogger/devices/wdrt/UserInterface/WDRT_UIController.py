from queue import SimpleQueue
from tkinter import Tk, TclError
from RSLogger.devices.wdrt.UserInterface import WDRT_UIView, WDRT_UIConfig, WDRT_UIPlotter


class WDRTUIController:
    def __init__(self, win, q_out, q_in):
        self._win: Tk = win
        self._q_in: SimpleQueue = q_in
        self._q_out: SimpleQueue = q_out

        self.devices = dict()

        # Experiment
        self._running = False

        # UserInterface
        self._win.bind("<<NotebookTabChanged>>", self._tab_changed_cb)
        self._view = WDRT_UIView.WDRTMainWindow(win, q_out)
        self._view.register_stim_on_cb(self._stim_on_button_cb)
        self._view.register_stim_off_cb(self._stim_off_button_cb)
        self._view.register_configure_clicked_cb(self._configure_button_cb)
        self._view.register_rescan_network(self._rescan_network_cb)
        self._active_tab = None

        # Configure Window
        self._cnf_win = WDRT_UIConfig.WDRTConfigWin(q_out)
        self._cnf_win.register_custom_cb(self._custom_button_cb)
        self._cnf_win.register_iso_cb(self._iso_button_cb)

        self._listen_for_incoming_messages()

    def _listen_for_incoming_messages(self):
        while not self._q_in.empty():
            msg = self._q_in.get()
            kvals = msg.split(">")
            arg = kvals[1]

            # Main Controller Events
            if arg == 'init':
                self._log_init(kvals[2:])
            elif arg == 'close':
                self._log_close(kvals[2:])
            elif arg == 'start':
                self._data_record(kvals[2:])
            elif arg == 'stop':
                self._data_pause(kvals[2:])

            # Tab Events
            elif arg == 'devices':
                self._update_devices(kvals[2:])
            elif arg == 'remove':
                self._remove_tab(kvals[2:])

            # Plot Commands
            elif arg == 'clear':
                self._clear_plot()

            # Messages from DRT unit
            elif arg == 'cfg':
                self._update_configuration(kvals[2:])
            elif arg == 'stm':
                self._update_stim_state(kvals[2:])
            elif arg == 'dta':
                self._update_stim_data(kvals[2:])
            elif arg == 'bty':
                self._update_battery_soc(kvals[2:])
            elif arg == 'rt':
                self._update_rt(kvals[2:])
            elif arg == 'clk':
                self._update_clicks(kvals[2:])

            elif arg == 'fpath':
                self._update_file_path(kvals[2:])

            elif 'cond' in arg:
                self._update_condition_name(arg)

        self._win.after(10, self._listen_for_incoming_messages)

    def _update_devices(self, devices=None):
        units = list()
        try:
            if devices != ['']:
                units = devices[0].split(",")
                self._view.show()
            else:
                self._view.hide()

            to_add = set(units) - set(self.devices)
            if to_add:
                self._add_tab(to_add)
            to_remove = set(self.devices) - set(units)
            if to_remove:
                self._remove_tab(to_remove)

        except AttributeError:
            pass

    def _add_tab(self, dev_ids):
        for id_ in dev_ids:
            if id_ not in self.devices:
                self.devices[id_] = self._view.build_tab(id_)
                pass

    def _remove_tab(self, dev_ids):
        for id_ in dev_ids:
            if id_ in self.devices.keys():
                self.devices.pop(id_)
                self._view.NB.forget(self._view.NB.children[id_.lower()])

    # UserInterface Parent
    def _log_init(self, arg):
        for d in self.devices:
            self.devices[d]['refresh'].config(state='disabled')

    def _log_close(self, arg):
        for d in self.devices:
            self.devices[d]['refresh'].config(state='active')

    def _data_record(self, arg):
        self._running = True
        if self._active_tab:
            self.devices[self._active_tab]['plot'].run = True
            self.devices[self._active_tab]['plot'].clear_all()

    def _data_pause(self, arg):
        self._running = False
        if self._active_tab:
            self.devices[self._active_tab]['plot'].run = False

    def _update_file_path(self, arg):
        pass

    # Registered Callbacks with wDRT UserInterface
    def _tab_changed_cb(self, e):
        if self.devices:
            try:
                # Clean up old tab and device
                self._q_out.put(f"hi_wdrt>vrb_off>{self._active_tab}")
                if self._running:
                    self.devices[self._active_tab]['plot'].run = False
                    self.devices[self._active_tab]['plot'].clear_all()
                # Start new tab and device
                self._active_tab = self._view.NB.tab(self._view.NB.select(), "text")
                self._q_out.put(f"hi_wdrt>vrb_on>{self._active_tab}")
                self._q_out.put(f"hi_wdrt>get_bat>{self._active_tab}")
                if self._running:
                    self.devices[self._active_tab]['plot'].run = True
                    self.devices[self._active_tab]['plot'].clear_all()
            except Exception as e:
                print(f"vController _tab_changed_cb: {e}")

    def _stim_on_button_cb(self):
        self._q_out.put(f"hi_wdrt>stm_on>{self._active_tab}")

    def _stim_off_button_cb(self):
        self._q_out.put(f"hi_wdrt>stm_off>{self._active_tab}")

    def _configure_button_cb(self):
        self._cnf_win.show(self._active_tab)
        self._q_out.put(f"hi_wdrt>get_cfg>{self._active_tab}")

    def _rescan_network_cb(self):
        for c in self._view.NB.winfo_children():
            try:
                self._view.NB.forget(c)
            except TclError:
                pass
        self.devices.clear()
        self._q_out.put(f"hi_wdrt>net_scn>")
        self._view.hide()

    # Plotter
    def _update_stim_state(self, arg):
        kv = arg[0].split(' ')
        try:
            if self._running:
                self.devices[kv[1]]['plot'].state_update(kv[1], kv[0])
        except AttributeError:
            pass

    def _update_stim_data(self, arg):
        if self._running:
            unit_id, ts, trial_n, rt, clicks, dev_utc, bty = arg[0].strip().split(',')
            if unit_id == self._active_tab:
                if rt == "-1":
                    self.devices[unit_id]['plot'].rt_update(unit_id, -.0001)
                self.devices[unit_id]['rt'].set(-1)
                self.devices[unit_id]['trl_n'].set(trial_n)
                self.devices[unit_id]['clicks'].set(0)
                self._update_battery_soc(bty, unit_id)

    def _update_rt(self, arg):
        if self._running:
            unit_id, rt = arg[0].split(',')
            rt = round((int(rt) / 1000000), 2)
            self.devices[unit_id]['rt'].set(rt)
            self.devices[unit_id]['plot'].rt_update(unit_id, rt)

    def _update_clicks(self, arg):
        if self._running:
            unit_id, clicks = arg[0].split(',')
            self.devices[unit_id]['clicks'].set(clicks)

    def _update_battery_soc(self, arg, unit_id=None):
        soc = arg
        if isinstance(arg, list):
            unit_id, soc = arg[0].strip().split(',')

        p = int(soc) // 10
        for i in range(10):
            color = 'white'
            if p >= i + 1:
                color = 'black' if p > 2 else 'red'
            self.devices[unit_id][f'b_{i}'].config(bg=color)

    def _stop_plotter(self):
        self.devices[self._active_tab]['plot'].run = False

    def _clear_plot(self):
        self.devices[self._active_tab]['plot'].clear_all()

    # Configuration Window
    # ---- Registered Callbacks
    def _custom_button_cb(self, msg):
        self._q_out.put(f"hi_wdrt>set_cfg>{msg}, {self._active_tab}")

    def _iso_button_cb(self):
        self._q_out.put(f"hi_wdrt>set_iso>{self._active_tab}")

    # ---- msg from wDRT unit
    def _update_configuration(self, args):
        self._cnf_win.parse_config(args[0])
