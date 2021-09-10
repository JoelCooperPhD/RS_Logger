from queue import SimpleQueue
from tkinter import Tk, TclError
from devices.DRT_SFT.UserInterface import SFT_UIView, SFT_UIConfig


class SFTUIController:
    def __init__(self, win, hardware_interface_q_sft, user_interface_q_sft):
        self._win: Tk = win
        self._q2_sft_hi: SimpleQueue = hardware_interface_q_sft
        self._q2_sft_ui: SimpleQueue = user_interface_q_sft

        # Events
        self._events = {
            # Main Controller Events
            "init": self._log_init,
            "close": self._log_close,
            "record": self._data_record,
            "pause": self._data_pause,

            # Tab Events
            "devices": self._update_devices,
            "remove": self._remove_tab,

            # Plot Commands
            "clear": self._clear_plot,

            # Messages from wDRT unit
            "cfg": self._update_configuration,
            "stm": self._update_stim_state,
            "dta": self._update_stim_data,
            "bty": self._update_battery_soc,
            "rt":  self._update_rt,
            "clk": self._update_clicks,

        }

        self.devices = dict()

        # Experiment
        self._running = False

        # View
        self._win.bind("<<NotebookTabChanged>>", self._tab_changed_cb)
        self._UIView = SFT_UIView.SFTTabbedControls(self._win)
        self._UIView.register_vib_cb(self._vib_button_cb)
        self._UIView.register_led_cb(self._led_button_cb)
        self._UIView.register_aud_cb(self._aud_button_cb)

        self._UIView.register_configure_clicked_cb(self._configure_button_cb)

        self._active_tab = None

        # Configure Window
        self._cnf_win = SFT_UIConfig.SFTConfigWin(self._q2_sft_ui)
        self._cnf_win.register_custom_cb(self._custom_button_cb)
        self._cnf_win.register_iso_cb(self._iso_button_cb)

        self._handle_messages_from_sft_hardware_interface()

    def _handle_messages_from_sft_hardware_interface(self):
        while not self._q2_sft_ui.empty():
            msg = self._q2_sft_ui.get()
            try:
                kvals = msg.split(">")
                if len(kvals[1]):
                    self._events[kvals[0]](kvals[1:])
                else:
                    self._events[kvals[0]]()
            except Exception as e:
                print(f"SFT_UIController : {e}")

        self._win.after(1, self._handle_messages_from_sft_hardware_interface)

    def _update_devices(self, devices=None):
        units = list()
        if devices:
            units = devices[0].split(",")
            self._UIView.show()
        else:
            self._UIView.hide()

        to_add = set(units) - set(self.devices)
        if to_add:
            self._add_tab(to_add)
        to_remove = set(self.devices) - set(units)
        if to_remove:
            self._remove_tab(to_remove)

    def _add_tab(self, dev_ids):
        for id_ in dev_ids:
            if id_ not in self.devices:
                self.devices[id_] = self._UIView.build_tab(id_)
                pass

    def _remove_tab(self, dev_ids):
        for id_ in dev_ids:
            if id_ in self.devices.keys():
                self.devices.pop(id_)
                self._UIView.NB.forget(self._UIView.NB.children[id_.lower()])

    # View Parent
    def _log_init(self):
        for d in self.devices:
            self.devices[d]['refresh'].config(state='disabled')

    def _log_close(self):
        for d in self.devices:
            self.devices[d]['refresh'].config(state='active')

    def _data_record(self):
        self._running = True
        self.devices[self._active_tab]['plot'].run = True
        self.devices[self._active_tab]['plot'].clear_all()

    def _data_pause(self):
        self._running = False
        self.devices[self._active_tab]['plot'].run = False

    # Registered Callbacks with wDRT View
    def _tab_changed_cb(self, e):
        if self.devices:
            try:
                # Clean up old tab and device
                if self._running:
                    self.devices[self._active_tab]['plot'].run = False
                    self.devices[self._active_tab]['plot'].clear_all()
                # Start new tab and device
                self._active_tab = self._UIView.NB.tab(self._UIView.NB.select(), "text")

                if self._running:
                    self.devices[self._active_tab]['plot'].run = True
                    self.devices[self._active_tab]['plot'].clear_all()
            except Exception as e:
                print(f"vController _tab_changed_cb: {e}")

    def _vib_button_cb(self):
        self._q2_sft_hi.put(f"{self._active_tab}>vib>toggle")

    def _led_button_cb(self):
        self._q2_sft_hi.put(f"{self._active_tab}>led>toggle")

    def _aud_button_cb(self):
        self._q2_sft_hi.put(f"{self._active_tab}>aud>toggle")

    def _configure_button_cb(self):
        self._cnf_win.show(self._active_tab)
        self._q2_sft_hi.put(f"{self._active_tab}>cfg>get")

    # Plotter
    def _update_stim_state(self, arg):
        if self._running:
            self.devices[arg[1]]['plot'].state_update(arg[1], arg[0])

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
        self._q2_sft_hi.put(f"set_cfg>{msg}>{self._active_tab}")

    def _iso_button_cb(self):
        self._q2_sft_hi.put(f"set_iso>{self._active_tab}")

    # ---- msg from wDRT unit
    def _update_configuration(self, args):
        self._cnf_win.parse_config(args)
