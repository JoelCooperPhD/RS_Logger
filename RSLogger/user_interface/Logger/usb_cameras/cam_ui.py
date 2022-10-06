import time
from tkinter import IntVar, StringVar
from tkinter.ttk import LabelFrame, Checkbutton, Spinbox
from tkinter import Label
import win32com.client
import cv2
from multiprocessing import Process, Pipe
from RSLogger.user_interface.Logger.usb_cameras import cam_win
from threading import Thread
from tkinter import RIGHT


class CameraWidget:
    def __init__(self, root_win, widget_frame):
        self._win = root_win

        self._process_running = True

        # Label frame
        self._cam_lf = LabelFrame(widget_frame, text="Cameras")
        self._cam_lf.pack(side=RIGHT, fill='y', padx=2)
        self._cam_lf.grid_columnconfigure(0, weight=1)
        self._cam_lf.grid_rowconfigure(5, weight=1)

        # Camera Spinbox
        self._selected_camera = StringVar()
        self._selected_camera.set("Scanning...")
        self._attached_cameras = dict()
        self._connected_cameras = dict()
        self._cam_sb = self._build_cameras_spinbox()

        # Use Camera Settings
        self._use_camera_var = IntVar()
        self._use_camera_var.set(0)
        self._build_use_camera_setting()

        # Resolution Settings
        self._selected_resolution = StringVar()
        self._selected_resolution.set("Low")
        self._build_resolution_setting()

        # Frame Rate Settings
        self._selected_frame_rate = StringVar()
        self._selected_frame_rate.set("10")
        self._build_frame_rate_settings()

        # Camera Connections and Communications
        self._prior_cam_count = int()
        self._cam_parent_pipe = dict()
        self._cam_pipe_msg_handler()
        self._update_connected_cameras()

        # Experiment Variables
        self._file_path = ""
        self.log_running = False
        self.record_running = False

    def set_file_path(self, file_path):
        self._file_path = file_path

    ########################
    # Controls
    def handle_log_init(self, val):
        try:
            for c in self._cam_parent_pipe:
                self._cam_parent_pipe[c].send(f"FNM>{self._file_path}")
                self._cam_parent_pipe[c].send("RCD>1")
            for c in self._cam_lf.winfo_children():
                c.configure(state="disabled")
        except Exception as e:
            print(e)

    def handle_log_close(self, val):
        try:
            self.log_running = False
            for c in self._cam_parent_pipe:
                self._cam_parent_pipe[c].send("RCD>0")
            for c in self._cam_lf.winfo_children():
                c.configure(state="normal")
        except Exception as e:
            print(e)

    def handle_data_record(self, val):
        self.record_running = True

    def handle_data_pause(self, val):
        self.record_running = False

    ########################
    # Build Widget
    def _build_cameras_spinbox(self):
        sb = Spinbox(self._cam_lf, textvar=self._selected_camera, values=[],
                     command=self._cb_cam_selected, state='readonly')
        sb.grid(row=0, column=0, columnspan=2)
        return sb

    def _build_use_camera_setting(self):
        self._use_cb = Checkbutton(self._cam_lf, text="Use Camera", command=self._cb_use_selected,
                                   variable=self._use_camera_var, onvalue=1, offvalue=0)
        self._use_cb.grid(row=1, column=0, columnspan=2, sticky="W")

    def _build_resolution_setting(self):
        Label(self._cam_lf, text="Resolution").grid(row=2, column=0, sticky="W")
        self._res_sb = Spinbox(self._cam_lf, textvar=self._selected_resolution, command=self._cb_resolution_selected,
                               values=("Low", "Medium", "High", "HD"), width=10, state='readonly')
        self._res_sb.grid(row=2, column=1)

    def _build_frame_rate_settings(self):
        rates = ('1', '5', '10', '15', '20', '25', '30')
        Label(self._cam_lf, text="FPS").grid(row=3, column=0, sticky="W")
        self._fps_sb = Spinbox(self._cam_lf, textvar=self._selected_frame_rate, command=self._cb_fps_selected,
                               values=rates, width=10, state='readonly')
        self._fps_sb.grid(row=3, column=1)

    ########################
    # Select Cameras
    def _cb_cam_selected(self):
        cam = self._selected_camera.get()
        if cam != 'Scanning...' and cam != '0':
            if cam in list(self._attached_cameras.keys()):
                self._use_camera_var.set(self._attached_cameras[cam]['use'])
                self._selected_resolution.set(self._attached_cameras[cam]['res'])
                self._selected_frame_rate.set(self._attached_cameras[cam]['FPS'])
        else:
            self._selected_camera.set('Scanning...')

    def _cb_use_selected(self):
        cam = self._selected_camera.get()
        if cam != 'Scanning...':
            val = self._use_camera_var.get()
            self._attached_cameras[cam]['use'] = val

            try:
                if val == 0:
                    self._cam_parent_pipe[cam].send(f"{cam}-USE>{cam}")
                else:
                    self._connect_cameras(cam)
            except BrokenPipeError:
                pass

    def _cb_resolution_selected(self):
        cam = self._selected_camera.get()
        if cam != 'Scanning...':
            self._attached_cameras[cam]['res'] = self._selected_resolution.get()
            if cam in self._cam_parent_pipe:
                self._cam_parent_pipe[cam].\
                    send(f"{cam}-RES>{self._selected_resolution.get()}")

    def _cb_fps_selected(self):
        cam = self._selected_camera.get()
        if cam != 'Scanning...':
            self._attached_cameras[cam]['FPS'] = self._selected_frame_rate.get()
            if cam in self._cam_parent_pipe:
                self._cam_parent_pipe[cam]. \
                    send(f"{self._selected_camera.get()}-FPS>{self._selected_frame_rate.get()}")

    def _connect_cameras(self, cam_id):
        cam = cam_id.split(':')[1]
        self._cam_parent_pipe[cam_id], child_pipe = Pipe()
        self._connected_cameras[cam_id] = Process(target=cam_win.CamViewer, args=(cam_id, child_pipe))
        self._connected_cameras[cam_id].start()

        fps = self._attached_cameras[self._selected_camera.get()]['FPS']
        res = self._attached_cameras[self._selected_camera.get()]['res']

        self._cam_parent_pipe[cam_id].send(f"{cam}-FPS>{fps}")
        self._cam_parent_pipe[cam_id].send(f"{cam}-RES>{res}")

        self._cam_parent_pipe[cam_id].send(f"{cam}-SHW>{cam}")


    ########################
    # Attach new cameras
    def _update_connected_cameras(self):
        """
        Detects a change in the number of attached usb devices.
        If there is a change then it reaches out to the camera controller to notify it.
        If a camera is unplugged, it is removed
        """
        if self._process_running:
            wmi = win32com.client.GetObject("winmgmts:")
            usb_items = wmi.InstancesOf("Win32_USBHub")
            usb_num_delta = self._prior_cam_count - len(usb_items)
            self._prior_cam_count = len(usb_items)

            if usb_num_delta != 0:
                time.sleep(1)
                available_cams = self._identify_available_cameras()

                # Update camera dictionary with current cameras
                new_cams = set(available_cams)
                old_cams = set(list(self._attached_cameras.keys()))
                for i in (new_cams - old_cams):
                    self._attached_cameras[i] = {'use': 0, 'res': 'Low', 'FPS': '10'}
                for i in (old_cams - new_cams):
                    self._attached_cameras.pop(i)
                    self._cb_cam_selected()

                # Update SpinBox with correct camera information
                if len(available_cams) > 0:
                    self._selected_camera.set(available_cams[0])
                    self._cam_sb.config(value=available_cams[::-1])
                    self._cb_cam_selected()

                else:
                    self._selected_camera.set('Scanning...')

            self._win.after(500, self._update_connected_cameras)


    @staticmethod
    def _identify_available_cameras():
        attached_cameras = list()
        for i in range(4):
            cam = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cam.isOpened():
                attached_cameras.append(f'CAMERA:{i}')
                t = Thread(target=cam.release)
                t.start()
        return attached_cameras

    ########################
    # Messaging
    def _cam_pipe_msg_handler(self):
        """ Checks all camera pipes for a new message. New messages are then handled """
        pop = None
        if self._process_running:
            for i in self._cam_parent_pipe:
                try:
                    if self._cam_parent_pipe[i].poll():
                        msg: str = self._cam_parent_pipe[i].recv()
                        kv = msg.split('-')
                        cmd, val = kv[1].split(':')
                        if cmd == 'USE':
                            self._attached_cameras[kv[0]]['use'] = val
                            self._use_camera_var.set(val)
                            pop = kv[0]

                except BrokenPipeError:
                    pass
                    # print(f"Camera {i} has been disconnected")
            if pop:
                self._cam_parent_pipe.pop(pop)
            self._win.after(200, self._cam_pipe_msg_handler)

