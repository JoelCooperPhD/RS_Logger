from queue import SimpleQueue
from tkinter import Tk
from RSLogger.user_interface.sDRT_UI import sDRT_UIConfig, sDRT_UIView


class sDRTUIController:
    def __init__(self, win, q_2_hi):
        self._win: Tk = win
        self._q_2_hi: SimpleQueue = q_2_hi

        self.devices = dict()

        # Experiment
        self._running = False

        # View
        # self._win.bind("<<NotebookTabChanged>>", self._drt_tab_changed_cb)
        self._UIView = sDRT_UIView.DRTTabbedControls(self._win)

        self._UIView.register_configure_clicked_cb(self._configure_button_cb)
        self._UIView.register_stimulus_on_cb(self._stimulus_on_cb)
        self._UIView.register_stimulus_off_cb(self._stimulus_off_cb)

        # Configure Window
        self._cnf_win = sDRT_UIConfig.DRTConfigWin(self._q_2_hi)

    def handle_command(self, com, key, val):
        # Tab Events
        if key == 'devices':
            self._update_devices(val)

        # Messages from drt hardware
        elif key == 'cfg':
            self._update_configuration(f'{com}, {val}')
        elif key == 'stm':
            self._update_stimulus_plot(f'{com}, {val}')
        elif key == 'trl':
            self._update_results(f'{com}, {val}')
        elif key == 'clk':
            self._update_response_text(f'{com}, {val}')

        # Plot Commands
        elif key == 'clear':
            self._clear_plot()

        # File Path
        elif key == 'fpath':
            pass

    def handle_control_command(self, key, val):
        # Main Controller Events
        if key == 'init':
            self._log_init()
        elif key == 'close':
            self._log_close()
        elif key == 'start':
            self._data_start()
        elif key == 'stop':
            self._data_stop()

    # Main Controller Events
    def _log_init(self, time_stamp=None):
        for d in self.devices:
            self.devices[d]['stm_on'].configure(state='disabled')
            self.devices[d]['stm_off'].configure(state='disabled')
            self.devices[d]['configure'].configure(state='disabled')
            self.devices[self._UIView.NB.tab(self._UIView.NB.select(), "text")]['plot'].clear_all()

    def _log_close(self, time_stamp=None):
        for d in self.devices:
            self.devices[d]['stm_on'].configure(state='normal')
            self.devices[d]['stm_off'].configure(state='normal')
            self.devices[d]['configure'].configure(state='normal')

    def _data_start(self, time_stamp=None):
        self._running = True
        for d in self.devices:
            self.devices[d]['plot'].run = True
            self.devices[d]['plot'].clear_all()
            self._reset_results_text()

    def _data_stop(self, time_stamp=None):
        self._running = False
        for d in self.devices:
            self.devices[d]['plot'].run = False

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
                    self._q_2_hi.put(f'sDRT>all>stop>1')
                    pass

        to_remove = set(self.devices) - set(units)
        if to_remove:
            for id_ in to_remove:
                if id_ in self.devices.keys():
                    self.devices.pop(id_)
                    self._UIView.NB.forget(self._UIView.NB.children[id_.lower()])

    # Messages from drt hardware
    def _update_configuration(self, args):
        self._cnf_win.update_fields(args)

    def _update_stimulus_plot(self, arg):
        port, state = arg.split(',')
        if self._running:
            self.devices[port]['plot'].state_update(port, state)

            if state == '1':
                self._update_response_text(f'{port},0')

    def _update_rt_plot(self, arg):
        if self._running:
            unit_id, rt = arg.split(',')
            rt = int(rt)
            rt = -0.1 if rt == -1 else round((int(rt) / 1000), 2)
            self.devices[unit_id]['plot'].rt_update(unit_id, rt)

    def _update_results(self, arg):
        arg_split = arg.split(',')

        if len(arg_split) == 5:
            unit_id, unix_t, mills, trl_n, rt = arg_split
        else:
            unit_id, mills, trl_n, rt = arg_split

        self._update_trial_text(unit_id, trl_n)
        self._update_rt_text(unit_id, rt)
        self._update_rt_plot(f'{unit_id}, {rt}')

    def _reset_results_text(self):
        for d in self.devices:
            self._update_trial_text(d, '0')
            self._update_rt_text(d, '-1')
            self._update_response_text(f'{d},0')

    def _update_trial_text(self, unit_id, cnt):
        if self._running:
            self.devices[unit_id]['trl_n'].set(cnt)

    def _update_rt_text(self, unit_id, rt):
        if self._running:
            if rt != '-1':
                rt = round((int(rt) / 1000), 2)
            self.devices[unit_id]['rt'].set(rt)

    def _update_response_text(self, msg):
        unit_id, clicks = msg.split(',')
        if self._running:
            self.devices[unit_id]['clicks'].set(clicks)

    # Plot Commands
    def _clear_plot(self):
        for d in self.devices:
            self.devices[d]['plot'].clear_all()

    def _stop_plotter(self):
        for d in self.devices:
            self.devices[d]['plot'].run = False

    def _stimulus_on_cb(self):
        self._q_2_hi.put(f"sDRT>{self._UIView.NB.tab(self._UIView.NB.select(), 'text')}>stim>on")

    def _stimulus_off_cb(self):
        self._q_2_hi.put(f"sDRT>{self._UIView.NB.tab(self._UIView.NB.select(), 'text')}>stim>off")

    def _configure_button_cb(self):
        self._cnf_win.show(self._UIView.NB.tab(self._UIView.NB.select(), "text"))
        self._q_2_hi.put(f"sDRT>{self._UIView.NB.tab(self._UIView.NB.select(), 'text')}>get_config>")

