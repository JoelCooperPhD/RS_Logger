from tkinter import scrolledtext, END, LEFT
from tkinter.ttk import Button, LabelFrame
from time import time
from threading import Thread


class NoteTaker:
    def __init__(self, widget_frame):
        self._widget_frame = widget_frame

        self._file_path = None

        # Widget Variables
        self.note = ""

        self._widget_lf = LabelFrame(widget_frame, text='Note')
        self._widget_lf.pack(side=LEFT, fill='y', padx=2)
        self._widget_lf.grid_columnconfigure(0, weight=1)
        self._widget_lf.grid_rowconfigure(0, weight=1)

        self.note_text = scrolledtext.ScrolledText(self._widget_lf, height=3, width=25, state='disabled')
        self.note_text.grid(row=0, column=0, padx=2, pady=2)

        self.post_button = Button(self._widget_lf, text="Post", command=self._note_post_cb, state='disabled')
        self.post_button.grid(row=1, column=0, sticky='NEWS', pady=2, padx=2)

    def set_file_path(self, file_path):
        self._file_path = file_path

    ################################
    # Parent widget overrides
    def handle_log_init(self, timestamp):
        self.note_text['state'] = 'normal'
        self.post_button['state'] = 'normal'

    def handle_log_close(self, timestamp):
        self.note_text['state'] = 'disabled'
        self.post_button['state'] = 'disabled'

    def handle_data_record(self, timestamp):
        pass

    def handle_data_pause(self, timestamp):
        pass

    ################################
    # Widget callbacks
    def _note_post_cb(self):
        timestamp = time()
        self.note = self.note_text.get("1.0", END)
        self.note = self.note.strip()

        self.note_text.delete("1.0", END)

        self._log_note(self.note, timestamp)

    def _log_note(self, note, timestamp):
        def _write(_path, _results):
            try:
                with open(_path, 'a') as writer:
                    writer.write(_results + '\n')
            except PermissionError:
                print("Note write error")

        data = f"Note,{note},{timestamp}"
        file_path = f"{self._file_path}/notes.txt"

        t = Thread(target=_write, args=(file_path, data))
        t.start()


