from queue import SimpleQueue
from tkinter import Tk, TclError
from devices.drt.UserInterface import DRT_UIView, DRT_UIConfig


class drtUIController:
    def __init__(self, win, q_out, q_in):
        self._win: Tk = win
        self._q_out: SimpleQueue = q_out
        self._q_in: SimpleQueue = q_in

        self.devices = dict()

        # Experiment
        self._running = False

        # View
        self._win.bind("<<NotebookTabChanged>>", self._tab_changed_cb)
        self._UIView = DRT_UIView.drtTabbedControls(self._win)
        self._UIView.register_stim_l_cb(self._stimulus_toggle_cb)

        self._UIView.register_configure_clicked_cb(self._configure_button_cb)

        self._active_tab = None

        # Configure Window
        self._cnf_win = DRT_UIConfig.drtConfigWin(self._q_out)

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

            # Messages from drt hardware
            elif key == 'cnf':
                self._update_configuration(val)
            elif key == 'stm':
                self._update_stimulus_state(val)
            elif key == 'trl':
                self._update_trial_num(val)
            elif key == 'rt':
                self._update_rt(val)
            elif key == 'clk':
                self._update_clicks(val)

            # Plot Commands
            elif key == 'clear':
                self._clear_plot()

            # File Path
            elif key == 'fpath':
                pass

        self._win.after(10, self._queue_monitor)

    # Main Controller Events
    def _log_init(self, time_stamp=None):
        for d in self.devices:
            for c in self.devices[d]['lf'].winfo_children():
                c.configure(state="disabled")
            self.devices[d]['configure'].configure(state='disabled')

    def _log_close(self, time_stamp=None):
        for d in self.devices:
            for c in self.devices[d]['lf'].winfo_children():
                c.configure(state="normal")
            self.devices[d]['configure'].configure(state='normal')

    def _data_start(self, time_stamp=None):
        self._running = True
        if self.devices:
            self.devices[self._active_tab]['plot'].run = True
            self.devices[self._active_tab]['plot'].clear_all()

    def _data_stop(self, time_stamp=None):

        self._running = False
        if self.devices and self._active_tab:
            self.devices[self._active_tab]['plot'].run = False

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

    # Messages from drt hardware
    def _update_configuration(self, args):
        self._cnf_win.parse_config(args)

    def _update_stimulus_state(self, arg):
        port, state = arg.split(',')
        if self._running:
            self.devices[port]['plot'].state_update(port, state)

    def _update_trial_num(self, arg):
        if self._running:
            unit_id, cnt = arg.split(',')
            self.devices[unit_id]['trl_n'].set(cnt)

    def _update_rt(self, arg):
        if self._running:
            unit_id, rt = arg.split(',')
            if int(rt) != -1:
                rt = round((int(rt) / 1000), 2)
            else:
                rt = -.001
            self.devices[unit_id]['rt'].set(rt)
            self.devices[unit_id]['plot'].rt_update(unit_id, rt)

    def _update_clicks(self, arg):
        if self._running:
            unit_id, clicks = arg.split(',')
            self.devices[unit_id]['clicks'].set(clicks)

    # Plot Commands
    def _clear_plot(self):
        self.devices[self._active_tab]['plot'].clear_all()

    def _stop_plotter(self):
        self.devices[self._active_tab]['plot'].run = False

    # Registered Callbacks with drt UIView
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

    def _stimulus_toggle_cb(self):
        self._q_out.put(f"hi_drt>VIB.L>{self._active_tab}")

    def _configure_button_cb(self):
        self._cnf_win.show(self._active_tab)
        self._q_out.put(f"hi_drt>config>{self._active_tab}")

