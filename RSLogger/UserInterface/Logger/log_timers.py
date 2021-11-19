from tkinter import IntVar, StringVar, LEFT
from tkinter.ttk import Label, LabelFrame
from datetime import datetime


class InfoDisplay:
    def __init__(self, widget_frame, q2v):
        self._widget_frame = widget_frame

        self._q2v = q2v

        self._log_initialized = False
        self._data_recording = False

        # Main widget label frame
        self._widget_lf = LabelFrame(widget_frame, text='Log Timers')
        self._widget_lf.pack(side=LEFT, fill='y', padx=2)

        self._log_init_t = datetime.now()
        self._record_start_t = datetime.now()

        # Time
        self._var_time = StringVar()
        self._var_time.set("N/A")

        Label(self._widget_lf, text="Current time:"). \
            grid(row=0, column=0, sticky='W')

        Label(self._widget_lf, textvariable=self._var_time). \
            grid(row=0, column=1, sticky='E')

        # Exp initialize time
        self._var_log_start_time = StringVar()
        self._log_timer_clear()

        Label(self._widget_lf, text="Log Initialize Time:") \
            .grid(row=1, column=0, sticky='W')

        Label(self._widget_lf, textvariable=self._var_log_start_time) \
            .grid(row=1, column=1, sticky='E')

        # block start time
        self._var_record_start_time = StringVar()
        self._rec_timer_clear()

        Label(self._widget_lf, text="Data Record Time:") \
            .grid(row=2, column=0, sticky='W')

        Label(self._widget_lf, textvariable=self._var_record_start_time) \
            .grid(row=2, column=1, sticky='E')

        # block number
        self._var_entries_count = IntVar()
        self._var_entries_count.set(0)

        Label(self._widget_lf, text="Data Record Entries:") \
            .grid(row=3, column=0, sticky='W')

        Label(self._widget_lf, textvariable=self._var_entries_count) \
            .grid(row=3, column=1, sticky='E')

        self._refresh_times()

    ################################
    # Parent widget overrides
    def handle_log_init(self, timestamp):
        self._log_timer_start()
        self._rec_timer_clear()
        self._rec_entries_clear()

    def handle_log_close(self, timestamp):
        self._log_timer_stop()

    def handle_data_record(self, timestamp):
        self._rec_timer_start()
        self._rec_entries_augment()

    def handle_data_pause(self, timestamp):
        self._rec_timer_stop()

    ################################
    # Class helper functions
    def _log_timer_start(self):
        self._log_initialized = True
        self._log_init_t = datetime.now()

    def _log_timer_stop(self):
        self._log_initialized = False

    def _log_timer_clear(self):
        self._var_log_start_time.set('0:00:00.0')

    def _rec_timer_start(self):
        self._data_recording = True
        self._record_start_t = datetime.now()

    def _rec_timer_stop(self):
        self._data_recording = False

    def _rec_timer_clear(self):
        self._var_record_start_time.set('0:00:00.0')

    def _rec_entries_augment(self):
        self._var_entries_count.set(self._var_entries_count.get() + 1)

    def _rec_entries_clear(self):
        self._var_entries_count.set(0)

    def _refresh_times(self):
        now = datetime.now()

        self._var_time.set(now.strftime("%H:%M:%S:%f")[:-5])

        if self._log_initialized:
            self._var_log_start_time.set(str((now - self._log_init_t))[:-5])

        if self._data_recording:
            self._var_record_start_time.set(str((now - self._record_start_t))[:-5])

        self._widget_lf.after(100, self._refresh_times)


