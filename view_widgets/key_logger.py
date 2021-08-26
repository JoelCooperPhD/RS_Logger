from tkinter import StringVar, Tk, RIGHT, LEFT
from tkinter.ttk import Label, Button, LabelFrame
from time import time
from threading import Thread


class KeyFlagger:
    def __init__(self, win: Tk, widget_frame):

        self._win = win
        self._win.bind("<Key>", self._key_event)

        self._file_path = None
        self._var_displayed_key = StringVar()
        self._var_displayed_key.set("NA")

        # Main widget label frame
        self._widget_lf = LabelFrame(widget_frame, text='Key Logger')
        self._widget_lf.pack(side=LEFT, fill='y', padx=2)
        self._widget_lf.grid_columnconfigure(0, weight=1)
        self._widget_lf.grid_rowconfigure(0, weight=1)

        # Pressed key label
        self._label_key = Label(self._widget_lf, textvariable=self._var_displayed_key, font=20, state='disabled')
        self._label_key.grid(row=0, column=0)

        # Use widget button
        self._button_use = Button(self._widget_lf, text="Set Focus", state='disabled', command=self._use_button_cb)
        self._button_use.grid(row=1, column=0, sticky="NEWS", padx=2, pady=2)

    def set_file_path(self, file_path):
        self._file_path = file_path

    ################################
    # Widget callbacks
    def handle_log_init(self, timestamp):
        self._label_key['state'] = 'normal'
        self._button_use['state'] = 'normal'

    def handle_log_close(self, timestamp):
        self._label_key['state'] = 'disabled'
        self._button_use['state'] = 'disabled'

    def _key_event(self, e):
        timestamp = time()

        if str(self._win.focus_get()) != ".!frame.!labelframe2.!button":
            self._label_key['state'] = 'disabled'
        else:
            self._label_key['state'] = 'normal'

        if str(self._label_key.cget('state')) == 'normal':
            self._var_displayed_key.set(e.char)

            if self._file_path:
                self._log_key_event(e.char, timestamp)

    def _log_key_event(self, event, timestamp):
        def _write(_path, _results):
            try:
                with open(_path, 'a') as writer:
                    writer.write(_results + '\n')
            except PermissionError:
                print("Keylog write error")

        data = f"keyflag,{event},{timestamp}"
        file_path = f"{self._file_path}/keyflags.txt"

        t = Thread(target=_write, args=(file_path, data))
        t.start()

    @staticmethod
    def _use_button_cb():
        pass


