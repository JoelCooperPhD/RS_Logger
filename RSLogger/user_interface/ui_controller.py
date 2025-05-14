import urllib.request
import webbrowser
import inspect

from urllib.error import URLError
from tkinter import Tk, BOTH, messagebox, Canvas, Label
from tkinter.ttk import Frame
from os import path

from time import time_ns
from queue import SimpleQueue
from main import __version__

# User Interface
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
    def __init__(self, queues, debug=False):
        self._debug = debug
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}")

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

        # XBee connection status
        self.xbee_connected = False
        self.xbee_port = ""
        
        # Main widget frame - using grid for consistent layout
        self.widget_frame = Frame(self.win)
        self.widget_frame.pack(fill=BOTH)
        self.widget_frame.columnconfigure(4, weight=1)
        
        # Create separate frame for connection indicator to avoid mixing grid/pack
        self.conn_frame_container = Frame(self.win)
        self.conn_frame_container.pack(anchor='ne', padx=5, pady=2)
        
        # Create a better formatted connection label
        Label(self.conn_frame_container, text="Wireless Dongle:", font=("Arial", 8)).pack(side='left')
        
        # Connection status indicator (circle)
        self.conn_indicator = Canvas(self.conn_frame_container, width=10, height=10, bd=0, highlightthickness=0)
        self.conn_indicator.pack(side='left', padx=(5, 2))
        self.conn_circle = self.conn_indicator.create_oval(1, 1, 9, 9, fill="red", outline="")
        
        # Connection port label
        self.conn_port_var = "NOT CONNECTED"
        self.conn_port_label = Label(self.conn_frame_container, text=self.conn_port_var, font=("Arial", 8, "bold"))
        self.conn_port_label.pack(side='left')

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
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}")

        while not self._q_2_ui.empty():

            msg = self._q_2_ui.get()
            try:
                device, port, key, val = msg.split('>')
                # Handle XBee connection status
                if device == 'xbee' and key == 'conn_status':
                    self._update_connection_indicator(val)
                elif device in self._device_controllers.keys():
                    self._device_controllers[device].handle_command(port, key, val)
            except ValueError as e:
                pass

        self.win.after(10, self._q_2_ui_messages_listener)
        
    def _update_connection_indicator(self, status_str):
        """Update the XBee connection indicator based on status string."""
        # Format: "connected|port_name" or "disconnected"
        if status_str.startswith("connected|"):
            self.xbee_connected = True
            self.xbee_port = status_str.split("|")[1]
            self.conn_indicator.itemconfig(self.conn_circle, fill="green")
            self.conn_port_label.config(text=f"CONNECTED on {self.xbee_port}")
        else:
            self.xbee_connected = False
            self.xbee_port = ""
            self.conn_indicator.itemconfig(self.conn_circle, fill="red")
            self.conn_port_label.config(text="NOT CONNECTED")

    def _control_handler(self, key, val):
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}")

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

    def check_version(self):
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}")

        try:
            version = urllib.request.urlopen("https://raw.githubusercontent.com/redscientific/RS_Logger/master/version.txt")
            version = str(version.read().decode('utf-8'))
            version = version.strip()
            if version > __version__:
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

    def file_(self):
        return path.basename(__file__)

    def class_(self):
        return self.__class__.__name__

    def method_(self):
        return  inspect.currentframe().f_back.f_code.co_name




