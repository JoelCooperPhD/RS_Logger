from tkinter import Tk, BOTH
import tkinter.ttk as ttk
from queue import SimpleQueue
from os import path
from time import sleep

from view_widgets.controls import ExpControls
from view_widgets.key_logger import KeyFlagger
from view_widgets.note_logger import NoteTaker
from view_widgets.log_timers import InfoDisplay

from devices.DRT_SFT.UserInterface import SFT_UIController


class MainWindow:
    def __init__(self, queues):
        self._queues = queues
        self._q_in = queues['ui_root']
        self._q_out = queues['main']

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

        self._widgets = {'control': ExpControls(self._widget_frame, self._q_out),
                         'key_flag': KeyFlagger(self._win, self._widget_frame),
                         'note': NoteTaker(self._widget_frame, self._q_out),
                         'info': InfoDisplay(self._widget_frame, self._q_out)}

        self._queue_monitor()

        # Devices
        self._devices = {'DRT_SFT': SFT_UIController.SFTUIController(self._win,
                                                                     self._q_out,
                                                                     self._queues['ui_sft'])}

        # Tkinter loop
        self._win.protocol("WM_DELETE_WINDOW", self._close_event)
        self._win.mainloop()

    def _queue_monitor(self):
        while not self._q_in.empty():
            msg = self._q_in.get()
            address, key, val = msg.split(">")
            if key == 'fpath':
                self._update_file_paths(val)

            elif key in ['init', 'close', 'start', 'stop']:
                self._handle_new_logger_command(key, val)

        self._win.after(100, self._queue_monitor)

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

    def _handle_new_logger_command(self, key, val):
        for w in self._widgets:
            try:
                if key == 'init':
                    self._widgets[w].handle_log_init(val)
                elif key == 'close':
                    self._widgets[w].handle_log_close(val)
                elif key == 'start':
                    self._widgets[w].handle_data_record(val)
                elif key == 'stop':
                    self._widgets[w].handle_data_pause(val)
            except AttributeError:
                pass

    def _close_event(self):
        print("closing...")
        self._q_out.put("exit")
        sleep(.05)
        self._win.destroy()
        exit()
