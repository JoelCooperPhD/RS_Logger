from queue import SimpleQueue
from tkinter import Tk, TclError
from devices.DRT_SFT.UserInterface import SFT_UIView, SFT_UIConfig


class SFTUIController:
    def __init__(self, win, hardware_interface_q_sft, user_interface_q_sft):
        self._win: Tk = win
        self._q2_sft_hi: SimpleQueue = hardware_interface_q_sft
        self._q2_sft_ui: SimpleQueue = user_interface_q_sft

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
        self._cnf_win = SFT_UIConfig.SFTConfigWin(self._q2_sft_hi)

        self._handle_incoming_messages()

    def _handle_incoming_messages(self):
        while not self._q2_sft_ui.empty():
            msg = self._q2_sft_ui.get()
            port, key, val = msg.split('>')

            if 'ALL' in msg:
                self._q2_sft_hi.put(msg)

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

            # Messages from SFT hardware
            elif key == 'cfg':
                self._update_configuration(val)
            elif key == 'stm':
                self._update_stimulus_state(val)
            elif key == 'rt':
                self._update_rt(val)
            elif key == 'clk':
                self._update_clicks(val)

            # Plot Commands
            elif key == 'clear':
                self._clear_plot()

        self._win.after(1, self._handle_incoming_messages)

    # Main Controller Events
    def _log_init(self, time_stamp=None):
        pass
        # refresh and disable charts
        # for d in self.devices:
        #     self.devices[d]['refresh'].config(state='disabled')

    def _log_close(self, time_stamp=None):
        pass
        # refresh and enable charts
        # for d in self.devices:
        #     self.devices[d]['refresh'].config(state='active')

    def _data_start(self, time_stamp=None):
        self._running = True
        self.devices[self._active_tab]['plot'].run = True
        self.devices[self._active_tab]['plot'].clear_all()

    def _data_stop(self, time_stamp=None):
        self._running = False
        self.devices[self._active_tab]['plot'].run = False

    # Tab Events
    def _update_devices(self, devices=None):
        units = list()
        if devices:
            units = devices[0].split(",")
            self._UIView.show()
        else:
            self._UIView.hide()

        to_add = set(units) - set(self.devices)
        if to_add:
            for id_ in to_add:
                if id_ not in self.devices:
                    self.devices[id_] = self._UIView.build_tab(id_)
                    pass

        to_remove = set(self.devices) - set(units)
        if to_remove:
            for id_ in to_remove:
                if id_ in self.devices.keys():
                    self.devices.pop(id_)
                    self._UIView.NB.forget(self._UIView.NB.children[id_.lower()])

    # Messages from SFT hardware
    def _update_configuration(self, args):
        self._cnf_win.parse_config(args)

    def _update_stimulus_state(self, arg):
        if self._running:
            self.devices[arg[1]]['plot'].state_update(arg[1], arg[0])

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

    # Plot Commands
    def _clear_plot(self):
        self.devices[self._active_tab]['plot'].clear_all()

    def _stop_plotter(self):
        self.devices[self._active_tab]['plot'].run = False

    # Registered Callbacks with SFT UIView
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
        self._q2_sft_hi.put(f"{self._active_tab}>vib")

    def _led_button_cb(self):
        self._q2_sft_hi.put(f"{self._active_tab}>led")

    def _aud_button_cb(self):
        self._q2_sft_hi.put(f"{self._active_tab}>aud")

    def _configure_button_cb(self):
        self._cnf_win.show(self._active_tab)
        self._q2_sft_hi.put(f"{self._active_tab}>config")

