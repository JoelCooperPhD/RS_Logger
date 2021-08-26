from tkinter import Tk, BOTH
import tkinter.ttk as ttk
from queue import SimpleQueue
from os import path
from time import sleep

from view_widgets.controls_logger import ExpControls
from view_widgets.key_logger import KeyFlagger
from view_widgets.note_logger import NoteTaker
from view_widgets.information import InfoDisplay

from devices.drt_sft import view as view_drt_sft


class MainWindow:
    def __init__(self, q2v, q2c):
        self._q2v: SimpleQueue = q2v
        self._q2c: SimpleQueue = q2c

        self._win: Tk = Tk()

        self._file_path = [None]

        self._win.resizable(True, True)
        self._win.title("Red Scientific Data Logger")
        path_to_icon = path.abspath(path.join(path.dirname(__file__), 'img/rs_icon.ico'))
        self._win.iconbitmap(path_to_icon)

        # Widgets
        self._widget_frame = ttk.Frame(self._win)
        self._widget_frame.pack(fill=BOTH)
        self._widget_frame.columnconfigure(4, weight=1)

        self._widgets = {'control': ExpControls(self._widget_frame, self._q2v),
                         'key_flag': KeyFlagger(self._win, self._widget_frame),
                         'note': NoteTaker(self._widget_frame, self._q2v),
                         'info': InfoDisplay(self._widget_frame, self._q2v)}

        self._monitor_q2v()

        # Devices
        self._devices = {'drt_sft': view_drt_sft.SFTUserInterface(self._win, q2v)}

        # Tkinter loop
        self._win.protocol("WM_DELETE_WINDOW", self._close_event)
        self._win.mainloop()

    def _monitor_q2v(self):
        while not self._q2v.empty():
            msg = self._q2v.get()
            kv = msg.split(">")

            if kv[0] == 'fpath':
                self._update_file_paths(kv[1])
            elif 'cmd' in msg:
                self._handle_new_logger_command(msg)
            else:
                print(f"view: {msg} event not handled")

        self._win.after(100, self._monitor_q2v)

    def _update_file_paths(self, file_path):
        for w in self._widgets:
            try:
                self._widgets[w].set_file_path(file_path)
            except AttributeError:
                pass
        '''
        for d in self._devices:
            try:
                self._devices[d].set_file_path(file_path)
            except AttributeError:
                pass
        '''

    def _handle_new_logger_command(self, msg):
        self._q2c.put(msg)
        time_stamp = msg.split(">")[1]
        for w in self._widgets:
            try:
                if 'init' in msg:
                    self._widgets[w].handle_log_init(time_stamp)
                elif 'close' in msg:
                    self._widgets[w].handle_log_close(time_stamp)
                elif 'record' in msg:
                    self._widgets[w].handle_data_record(time_stamp)
                elif 'pause' in msg:
                    self._widgets[w].handle_data_pause(time_stamp)
            except AttributeError:
                pass

    def _close_event(self):
        self._q2c.put("exit")
        sleep(.05)
        self._win.destroy()
        exit()
