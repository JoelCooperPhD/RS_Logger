from tkinter import StringVar, LEFT, filedialog
from tkinter.ttk import Button, Label, Entry, LabelFrame
from PIL import Image, ImageTk
from queue import SimpleQueue
from time import time
from os import path
from threading import Thread


class ExpControls:
    def __init__(self, widget_frame, q_out: SimpleQueue):

        self._q_out = q_out
        self._file_path = None

        # Main widget label frame
        self._widget_lf = LabelFrame(widget_frame, text='Controls')
        self._widget_lf.pack(side=LEFT)
        self._widget_lf.grid_columnconfigure(0, weight=1)
        self._widget_lf.grid_rowconfigure(0, weight=1)

        # Widget Variables
        self.var_cond_name = StringVar()

        # Init Log Button
        self._log_running = False
        self._log_button = Button(self._widget_lf, text="\nInitialize\n", command=self._log_button_cb)
        self._log_button.grid(row=0, column=0, pady=0, padx=2, sticky='NEWS', columnspan=2)

        # Record / Pause button
        self._record_running = False
        record_path = path.abspath(path.join(path.dirname(__file__), '../img/record.png'))
        pause_path = path.abspath(path.join(path.dirname(__file__), '../img/pause.png'))

        self._record_img = ImageTk.PhotoImage(Image.open(record_path))
        self._pause_img = ImageTk.PhotoImage(Image.open(pause_path))

        self._record_button = Button(self._widget_lf, image=self._record_img, command=self._record_button_cb)
        self._record_button.grid(row=0, column=2, pady=0, padx=2, sticky='NEWS')
        self._record_button.config(state="disabled")

        # Trial Name Entry
        Label(self._widget_lf, text="Label:", anchor='w') \
            .grid(row=1, column=0, pady=4, padx=2, sticky='NEWS')

        self.entry = Entry(self._widget_lf, textvariable=self.var_cond_name, width=20)
        self.entry.grid(row=1, column=1, pady=4, padx=2, sticky='EW', columnspan=2)


    def handle_log_init(self, timestamp):
        self._log_running = True
        self._record_button['state'] = "normal"
        self._log_button['text'] = "\nClose\n"
        self._log_controls('initialize', timestamp)

    def handle_log_close(self, timestamp):
        if self._record_running:
            self.handle_data_pause(timestamp)

        self._log_running = False
        self._record_button['state'] = 'disabled'
        self._log_button['text']="\nInitialize\n"
        self._log_controls('close', timestamp)

    def handle_data_record(self, timestamp):
        if not self._log_running:
            self._log_button_cb()

        if self._file_path:
            self._record_running = True
            self._log_button['state'] = 'disabled'
            self.entry['state'] = 'disabled'
            self._record_button.config(image=self._pause_img)
            self._log_controls('record', timestamp)

    def handle_data_pause(self, timestamp):
        self._record_running = False
        self.entry['state'] = 'normal'
        self._log_button['state'] = 'normal'
        self._record_button.config(image=self._record_img)
        self._log_controls('pause', timestamp)

    # File Paths
    def _ask_file_dialog(self):
        file_path = filedialog.askdirectory()
        if file_path:
            self._file_path = file_path
            self._q_out.put(f'main>fpath>{file_path}')
        else:
            self._file_path = None

    # Button Callbacks
    def _log_button_cb(self):
        timestamp = time()
        if not self._log_running:
            self._ask_file_dialog()
            if self._file_path:
                self.handle_log_init(timestamp)
                self._q_out.put(f'main>init>ALL')

        else:
            self.handle_log_close(timestamp)
            self._q_out.put(f'main>close>ALL')

    def _record_button_cb(self):
        timestamp = time()
        if not self._record_running:
            self.handle_data_record(timestamp)
            self._q_out.put(f'main>start>ALL')


        else:
            self._q_out.put(f'main>stop>ALL')
            self.handle_data_pause(timestamp)

    def _log_controls(self, state, timestamp):
        def _write(_path, _results):
            try:
                with open(_path, 'a') as writer:
                    writer.write(_results + '\n')
            except (PermissionError, FileNotFoundError):
                print("Control write error")

        data = f"control,{state},{timestamp}"
        file_path = f"{self._file_path}/controls.txt"

        t = Thread(target=_write, args=(file_path, data))
        t.start()
