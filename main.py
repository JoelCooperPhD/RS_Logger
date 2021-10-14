import asyncio
from threading import Thread
from queue import SimpleQueue
from multiprocessing import freeze_support
from os import path
from tkinter import Tk, ttk, BOTH

# Hardware Interface
from devices.drt_sft.HardwareInterface import SFT_HIController
from devices.drt.HardwareInterface import DRT_HIController
from devices.vog.HardwareInterface import VOG_HIController

# User Interface
from devices.drt_sft.UserInterface import SFT_UIController
from devices.drt.UserInterface import DRT_UIController
from devices.vog.UserInterface import VOG_UIController

# Widgets
from user_interface.controls import ExpControls
from user_interface.key_logger import KeyFlagger
from user_interface.note_logger import NoteTaker
from user_interface.log_timers import InfoDisplay
from user_interface.usb_cameras.cam_ui import CameraWidget


class Main:
    def __init__(self):
        self.run = True

        # Queues to communicate with the view and controller between threads
        self.queues = {'main': SimpleQueue(),

                       'user_interface': SimpleQueue(),

                       'hi_sft': SimpleQueue(),
                       'ui_sft': SimpleQueue(),

                       'hi_drt': SimpleQueue(),
                       'ui_drt': SimpleQueue(),

                       'hi_vog': SimpleQueue(),
                       'ui_vog': SimpleQueue()}

        # Controller Thread - This is a newly spawned thread where an asyncio loop is used
        self.t = Thread(target=self.async_controller_thread, daemon=True)
        self.t.start()

        # UserInterface Thread - This is the main thread where a tkinter loop is used
        self._win: Tk = Tk()

        self._file_path = [None]

        self._win.resizable(True, True)
        self._win.title("Red Scientific Data Logger")
        path_to_icon = path.abspath(path.join(path.dirname(__file__), '../RS_Logger/img/rs_icon.ico'))
        self._win.iconbitmap(path_to_icon)

        # Widgets
        self._widget_frame = ttk.Frame(self._win)
        self._widget_frame.pack(fill=BOTH)
        self._widget_frame.columnconfigure(4, weight=1)

        self._widgets = {'control': ExpControls(self._widget_frame, self.queues['main']),
                         'key_flag': KeyFlagger(self._win, self._widget_frame),
                         'note': NoteTaker(self._widget_frame, self.queues['main']),
                         'info': InfoDisplay(self._widget_frame, self.queues['main']),
                         'cam': CameraWidget(self._win, self._widget_frame, self.queues['main']),
                         }

        # Devices
        self._devices = {'sft': SFT_UIController.SFTUIController(self._win, self.queues['main'], self.queues['ui_sft']),
                         'drt': DRT_UIController.DRTUIController(self._win, self.queues['main'], self.queues['ui_drt']),
                         'vog': VOG_UIController.VOGUIController(self._win, self.queues['main'], self.queues['ui_vog'])
                         }

        # Tkinter loop
        self._win.mainloop()

    def async_controller_thread(self):
        asyncio.run(self.run_main_async())

    async def run_main_async(self):
        devices = {'SFT': SFT_HIController.SFTController(self.queues['main'], self.queues['hi_sft']),
                   'DRT': DRT_HIController.DRTController(self.queues['main'], self.queues['hi_drt']),
                   'VOG': VOG_HIController.VOGController(self.queues['main'], self.queues['hi_vog'])}
        for d in devices:
            devices[d].run()

        await asyncio.gather(self.main_message_router())

    async def main_message_router(self):
        while 1:
            while not self.queues['main'].empty():
                msg = self.queues['main'].get()
                if msg == 'exit':
                    print('Main: Handle Exit Stub')
                else:
                    address, key, val = msg.split('>')
                    if key in ['init', 'close', 'start', 'stop']:
                        self._handle_new_logger_command(key, val)
                    if address == 'main':
                        if val == 'ALL' or key == 'fpath':
                            if key == 'fpath':
                                self._update_file_paths(val)
                            for q in self.queues:
                                if q != 'main':
                                    self.queues[q].put(f'{q}>{key}>{val}')

                        if key in ['init', 'close', 'start', 'stop']:
                            self._handle_new_logger_command(key, val)
                    else:
                        self.queues[address].put(msg)
            await asyncio.sleep(.01)

    def _update_file_paths(self, file_path):
        for w in self._widgets:
            try:
                self._widgets[w].set_file_path(file_path)
            except AttributeError:
                pass

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

if __name__ == "__main__":
    freeze_support()
    Main()
