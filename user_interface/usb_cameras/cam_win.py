import asyncio
import sys

import cv2
import time
from numpy import zeros, std
from datetime import datetime
from multiprocessing import Pipe, Queue
from PIL import Image
import queue
from threading import Thread, Event
from time import sleep


class CameraReader:
    def __init__(self, cam_id, it_frame_q, cv2cr):
        """
        Asynchronous code run in a second thread. Handles all frame reads, text overlays, saves. Provides frames
        in a it_frame_q to main thread for display and is not blocked by changes in display position or size.

        :param cam_id: Provided at runtime as an integer
        :param ip_frame_p: Inter-process frame pipe
        :param it_frame_q: Inter-thread frame q
        :param show: Setting this event sends a flag to the main thread to display the video feed
        """
        self._it_frame_writer = it_frame_q
        self._id = int(cam_id.split(":")[1])
        self._show_window = False
        self._close = False

        self._cv2cr = cv2cr

        # Capture Properties
        self._cap = cv2.VideoCapture(int(self._id), cv2.CAP_DSHOW)
        # self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        # FPS Counter
        self._fps_last_frame_time = 0
        self._fps_array = zeros(60)
        self._fps_index = 0
        self._start_time = time.monotonic()
        self._actual_fps = 0

        # Frame write counters
        self._desired_fps = 30
        self._frame_count = 0
        self._frame_repeats = 0
        self._frame_drops = 0
        self._frame_tolerance = 3

        self._save_file_start_time = 0

        # Save Feed
        self._fpath = ""
        self._res = "Low"
        self._resolution = {"Low": (640, 480), "Medium": (960, 540), "High": (1280, 720), "HD": (1920, 1080)}
        self._record = False
        self._out = None

    async def capture(self):
        asyncio.create_task(self._monitor_cv2cr())
        while not self._close:
            try:
                ret, frame = await asyncio.get_running_loop().run_in_executor(None, self._cap.read)
                if frame is not None:
                    time_stamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                    fps, sd = self._fps_counter()
                    msg = f"{str(fps)} {self._desired_fps} {time_stamp}"
                    cv2.putText(frame, msg, (5, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                    if self._show_window:
                        self._it_frame_writer.put(frame)

                    if self._record:
                        self._save_camera_feed(frame)
                    elif self._out is not None:
                        self._out.release()
                        self._out = None
                else:
                    self._close = True
            except RuntimeError:
                pass
            await asyncio.sleep(.001)

    async def _monitor_cv2cr(self):
        while not self._close:
            while not self._cv2cr.empty():
                msg = self._cv2cr.get()
                kv = msg.split(">")
                if 'RCD' in kv[0]:
                    self._handle_save_video(kv)
                elif 'SHW' in kv[0]:
                    self._handle_show_win(kv)
                elif 'EXIT' in kv[0]:
                    self._handle_exit(kv)
                elif 'FNM' in kv[0]:
                    self._handle_set_fpath(kv)
                elif 'FPS' in kv[0]:
                    self._handle_set_fps(kv)
                elif 'RES' in kv[0]:
                    self._handle_set_resolution(kv)
                else:
                    print(f"CAM VIEW: {msg} event not handled")
            await asyncio.sleep(.001)

    def _handle_set_resolution(self, arg):
        low = self._resolution[arg[1]][0]
        high = self._resolution[arg[1]][1]
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, low)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, high)
        self._res = arg[1]

    def _handle_set_fps(self, arg):
        self._cap.set(cv2.CAP_PROP_FPS, int(arg[1]))
        self._desired_fps = int(arg[1])

    def _handle_set_fpath(self, arg):
        self._fpath = arg[1]

    def _handle_show_win(self, arg):
        self._show_window = True

    def _handle_exit(self, arg):
        self._show_window = False
        self._close = True

    def _handle_save_video(self, arg):
        if arg[1] == "1":
            self._frame_count = 0
            self._record = True
        else:
            self._record = False

    def _init_save(self):
        if self._record:
            fourcc = cv2.VideoWriter_fourcc(*'DIVX')
            path = f"{self._fpath}/cam_{self._id}.avi"
            fps_ = self._desired_fps
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            size = (w, h)
            writer = cv2.VideoWriter(path, apiPreference=1900, fourcc=fourcc, fps=fps_, frameSize=size, params=[])
            return writer
        else:
            return None

    def _save_camera_feed(self, frm):
        if not self._out:
            self._out = self._init_save()
            self._save_file_start_time = time.monotonic()

        fps_d = 1 / self._desired_fps
        run_time = time.monotonic() - self._save_file_start_time
        expected_frame_count = round(run_time / fps_d)

        ahead = self._frame_count - expected_frame_count >= self._frame_tolerance
        behind = expected_frame_count - self._frame_count >= self._frame_tolerance
        on_track = not ahead and not behind

        # I'm ahead, do nothing and the camera will catch up
        if ahead:
            self._frame_drops += 1

            # print(f" Drops: {self._frame_drops} Repeats: {self._frame_repeats}")

        # I'm behind, write frames until i'm no longer behind
        elif behind:
            while behind:
                self._frame_count += 1
                self._frame_repeats += 1
                self._out.write(frm)
                behind = expected_frame_count - self._frame_count >= 0

                # print(f" Drops: {self._frame_drops} Repeats: {self._frame_repeats}")

        # I'm on track! write a frame to stay that way
        elif on_track:
            self._frame_count += 1
            self._out.write(frm)

    def _fps_counter(self):
        # FPS counter
        current_frame_time = time.monotonic()

        d = current_frame_time - self._fps_last_frame_time
        self._fps_array[self._fps_index] = d
        self._fps_index += 1
        if self._fps_index == len(self._fps_array):
            self._fps_index = 0

        self._fps_last_frame_time = current_frame_time
        fps = round(1 / (sum(self._fps_array) / len(self._fps_array)))
        sd = std(self._fps_array)
        sd = round(float(sd), 4)

        return fps, sd


class CamViewer:
    def __init__(self, cam: str, ip_msg_p, exit_on_close=True):
        """
        Main thread for the camera viewer. Expects frames to be passed in from a separate thread over it_frame_q.
        Passing frames on a separate thread allows frames to be read in the background and not block when the View
        frame is moved or resized.

        :param cam_id: This is the computers id number for the camera
        :param cam_alias: This is the name given to the camera
        :param ip_msg_p: This is the child end of a 2-way pipe that is used to pass messages between processes
        :param ip_frame_q: Frames are read in the second async thread and passed to main thread for display
        :param exit_on_close: Setting to True terminates the process when the camera View is closed
        """
        self._cam_id = cam.split(":")[1]
        self._cam_alias = cam
        # Inter-process message Pipe and Queue
        self._ip_msg_p = ip_msg_p
        self._exit_on_close = exit_on_close
        # Inter-thread frame q. Frames are passed from the async thread to main thread View
        self._it_frame_q = queue.Queue()

        self._cv2cr = queue.Queue()

        self._show_window = False

        self._close = False

        # Cam controller async thread
        self._cam_c = Thread(target=self.controller_thread_entry,
                             args=(cam, self._it_frame_q, self._cv2cr))
        self._cam_c.start()

        self._events = {
            "USE": self._handle_exit_process,
            "RCD": self._handle_record,
            "SHW": self._handle_video_expand,
            "FNM": self._handle_set_file_name,
            "FPS": self._handle_set_fps,
            "RES": self._handle_set_resolution,
        }

        # Cam View main thread
        self._main_loop()

        if self._exit_on_close:
            sleep(1)

    def _main_loop(self):
        while not self._close:
            self._check_thread()
            self._check_for_new_messages()
            self._display_cam_view()
            sleep(.001)

    def _check_thread(self):
        # Thread dies when a camera is unplugged. If detected, kill the process
        if not self._cam_c.is_alive():
            self._cv2cr.put("EXIT")
            self._close = True
            self._show_window = False

    def _check_for_new_messages(self):
        try:
            if self._ip_msg_p.poll():
                msg = self._ip_msg_p.recv()
                kv = msg.split(">")
                if "USE" in kv[0]:
                    self._handle_exit_process(msg)
                elif "RCD" in kv[0]:
                    self._handle_record(msg)
                elif "SHW" in kv[0]:
                    self._handle_video_expand(msg)
                elif "FNM" in kv[0]:
                    self._handle_set_file_name(msg)
                elif "FPS" in kv[0]:
                    self._handle_set_fps(msg)
                elif "RES" in kv[0]:
                    self._handle_set_resolution(msg)
                else:
                    print("cam_popup message not handled")
        except (BrokenPipeError, EOFError):
            pass

    def _handle_set_resolution(self, arg):
        self._cv2cr.put(arg)

    def _handle_set_fps(self, arg):
        self._cv2cr.put(arg)

    def _handle_set_file_name(self, arg):
        self._cv2cr.put(arg)

    def _handle_video_expand(self, arg):
        self._cv2cr.put("SHW")
        self._show_window = True

    def _handle_exit_process(self, arg):
        if "0" in arg:
            self._cv2cr.put("EXIT")

    def _handle_record(self, arg):
        self._cv2cr.put(arg)

    def _display_cam_view(self):
        # Launches a new window to display frames read from the CameraReader passed over the it_frame_q
        if self._show_window:
            if not self._it_frame_q.empty():
                frame = self._it_frame_q.get()

                while not self._it_frame_q.empty():
                    frame = self._it_frame_q.get()

                cv2.namedWindow(self._cam_alias, cv2.WINDOW_NORMAL)
                cv2.imshow(self._cam_alias, frame)
                cv2.waitKey(1)

                if (cv2.getWindowProperty(str(self._cam_alias), cv2.WND_PROP_VISIBLE)) < 1:
                    self._show_window = False
                    if self._exit_on_close:
                        self._ip_msg_p.send(f'{self._cam_alias}-USE:0')
                        self._cv2cr.put("EXIT")


    # Controller Thread
    def controller_thread_entry(self, cam_num, it_frame_q, cv2cr):
        asyncio.run(self.controller(cam_num, it_frame_q, cv2cr))

    @staticmethod
    async def controller(cam_num, it_frame_q, cv2cr):
        reader = CameraReader(cam_num, it_frame_q, cv2cr)
        await(reader.capture())


if __name__ == "__main__":
    p, c = Pipe()
    q = Queue()
    CamViewer("Camera:0", p, True)

