import queue
import urllib.request
from urllib.error import URLError
import webbrowser
from tkinter import Tk, BOTH, messagebox
from tkinter.ttk import Frame
from os import path

from queue import SimpleQueue

from main import __version__

# User Interface
from RSLogger.user_interface.SFT_UI import SFT_UIController
from RSLogger.user_interface.sDRT_UI import sDRT_UIController
from RSLogger.user_interface.sVOG_UI import sVOG_UIController
from RSLogger.user_interface.wDRT_UI import wDRT_UIController
from RSLogger.user_interface.wVOG_UI import wVOG_UIController

# Widgets
from RSLogger.user_interface.Logger.controls import ExpControls
from RSLogger.user_interface.Logger.key_logger import KeyFlagger
from RSLogger.user_interface.Logger.note_logger import NoteTaker
from RSLogger.user_interface.Logger.log_timers import InfoDisplay
from RSLogger.user_interface.Logger.usb_cameras.cam_ui import CameraWidget


class UIController:
    def __init__(self, queues):
        self._q_2_ui: SimpleQueue = queues['q_2_ui']
        self._q_2_hi: SimpleQueue = queues['q_2_hi']

        # sDRT_UI Thread - This is the main thread where a tkinter loop is used
        self.win: Tk = Tk()
        self.win.withdraw()  # hide the window

        self.win.resizable(True, True)
        self.win.minsize(816, 105)
        self.win.title(f"RS Logger {__version__}")
        path_to_icon = path.abspath(path.join(path.dirname(__file__), '../img/rs_icon.ico'))
        self.win.iconbitmap(path_to_icon)

        # Widgets
        self.widget_frame = Frame(self.win)
        self.widget_frame.pack(fill=BOTH)
        self.widget_frame.columnconfigure(4, weight=1)

        self._widgets = {
            'controls': ExpControls(self.widget_frame, queues['q_2_hi'], self._control_handler),
            'key_flag': KeyFlagger(self.win, self.widget_frame),
            'note': NoteTaker(self.widget_frame),
            'info': InfoDisplay(self.widget_frame),
            'cam': CameraWidget(self.win, self.widget_frame),
        }

        # Devices
        self._device_controllers = {
            # 'sft': SFT_UIController.SFTUIController(self.win, queues['ui_controller'], queues['ui_sft']),
            'sDRT': sDRT_UIController.sDRTUIController(self.win, queues['q_2_hi']),
            'wDRT': wDRT_UIController.WDRTUIController(self.win, queues['q_2_hi']),
            'wVOG': wVOG_UIController.WVOGUIController(self.win, queues['q_2_hi']),
            'sVOG': sVOG_UIController.sVOGUIController(self.win, queues['q_2_hi'])
        }

        self._q_2_ui_messages_listener()

        self.check_version()

        # Tkinter loop
        self.win.after(0, self.win.deiconify)

        self.win.mainloop()

    def _q_2_ui_messages_listener(self):
        while not self._q_2_ui.empty():

            msg = self._q_2_ui.get()
            device, port, key, val = msg.split('>')
            if device in self._device_controllers.keys():
                self._device_controllers[device].handle_command(port, key, val)

        self.win.after(10, self._q_2_ui_messages_listener)

    def _control_handler(self, key, val):
        for widget in self._widgets:
            if key == 'fpath':
                self._widgets[widget].set_file_path(val)
            elif key == 'init':
                self._widgets[widget].handle_log_init(val)
            elif key == 'close':
                self._widgets[widget].handle_log_close(val)
            elif key == 'start':
                self._widgets[widget].handle_data_record(val)
            elif key == 'stop':
                self._widgets[widget].handle_data_pause(val)

        for controller in self._device_controllers:
            self._device_controllers[controller].handle_control_command(key, val)

    @staticmethod
    def check_version():
        try:
            version = urllib.request.urlopen("https://raw.githubusercontent.com/redscientific/RS_Logger/master/version.txt")
            version = str(version.read().decode('utf-8'))
            version = version.strip()
            if version != __version__:
                ans = messagebox.askquestion(
                    title="Notification",
                    message=f"You are running RSLogger version {__version__}\n\n"
                            f"The most recent version is {version}\n\n"
                            f"would you like to download the most recent version now?")
                if ans == 'yes':
                    url = f"https://github.com/redscientific/RS_Logger/raw/master/dist/Output/RSLogger_v{version}.exe"
                    webbrowser.open_new(url)
        except URLError:
            messagebox.showwarning(title="No Internet Connection!",
                                   message="Your software may be out of date.\n\n"
                                           "Please go to redscientific.com to check for updates.")




