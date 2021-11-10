import asyncio
from tkinter.ttk import LabelFrame, Label, Button, Entry
from tkinter import Toplevel, StringVar, messagebox, BOTH
from queue import SimpleQueue
from math import ceil
from PIL import Image, ImageTk
from os import path
from time import sleep


class SFTConfigWin:
    def __init__(self, q_out: SimpleQueue):
        self._q_out = q_out
        
        keys = ['HMS:0', 'HMS:1', 'HMS:2', 'HMS:3',
                'WS:LED', 'WS:VIB', 'WS:AUD',
                'HS:LED', 'HS:VIB', 'HS:AUD',
                'LED:L', 'LED:H',
                'VIB:L', 'VIB:H',
                'AUD:L', 'AUD:H',
                'ISI:L', 'ISI:H',
                'STM:DUR']

        values = [StringVar(), StringVar(), StringVar(), StringVar(),
                  StringVar(), StringVar(), StringVar(),
                  StringVar(), StringVar(), StringVar(),
                  StringVar(), StringVar(),
                  StringVar(), StringVar(),
                  StringVar(), StringVar(),
                  StringVar(), StringVar(),
                  StringVar()]

        self.UI_settings = dict(zip(keys, values))
        self.HW_settings = dict.fromkeys(keys, str())

        self._active_tab = None

    def show(self, uid):
        self._active_tab = uid

        win = Toplevel()
        win.grab_set()
        win.title("")
        path_to_icon = path.abspath(path.join(path.dirname(__file__), '../../../../rs_icon.ico'))
        win.iconbitmap(path_to_icon)
        win.focus_force()
        win.resizable(False, False)
        win.grid_columnconfigure(0, weight=1)

        # How Many Stimuli
        hms_lf = LabelFrame(win, text="Count Probabilities (%)")
        hms_lf.pack(padx=3)

        Label(hms_lf, text='HMS:0').grid(row=0, column=0)
        Label(hms_lf, text='HMS:1').grid(row=0, column=1)
        Label(hms_lf, text='HMS:2').grid(row=0, column=2)
        Label(hms_lf, text='HMS:3').grid(row=0, column=3)

        Entry(hms_lf, textvariable=self.UI_settings['HMS:0'], width=7).grid(row=1, column=0, sticky="W", padx=2)
        Entry(hms_lf, textvariable=self.UI_settings['HMS:1'], width=7).grid(row=1, column=1, sticky="W", padx=2)
        Entry(hms_lf, textvariable=self.UI_settings['HMS:2'], width=7).grid(row=1, column=2, sticky="W", padx=2)
        Entry(hms_lf, textvariable=self.UI_settings['HMS:3'], width=7).grid(row=1, column=3, sticky="W", padx=2)

        # Which Stimuli
        ws_lf = LabelFrame(win, text="Selection Probabilities (%)")
        ws_lf.pack(expand=True, fill=BOTH, pady=5, padx=3)

        Label(ws_lf, text="WS:LED").grid(row=0, column=0)
        Label(ws_lf, text="WS:VIB").grid(row=0, column=1)
        Label(ws_lf, text="WS:AUD").grid(row=0, column=2)

        Entry(ws_lf, textvariable=self.UI_settings['WS:LED'], width=7).grid(row=1, column=0, sticky="W", padx=2)
        Entry(ws_lf, textvariable=self.UI_settings['WS:VIB'], width=7).grid(row=1, column=1, sticky="W", padx=2)
        Entry(ws_lf, textvariable=self.UI_settings['WS:AUD'], width=7).grid(row=1, column=2, sticky="W", padx=2)

        # How Salient
        hs_lf = LabelFrame(win, text="Low Salience Stimulus Probabilities (%)")
        hs_lf.pack(expand=True, fill=BOTH, pady=5, padx=3)

        Label(hs_lf, text="HS:LED").grid(row=0, column=0)
        Label(hs_lf, text="HS:VIB").grid(row=0, column=1)
        Label(hs_lf, text="HS:AUD").grid(row=0, column=2)

        Entry(hs_lf, textvariable=self.UI_settings['HS:LED'], width=7).grid(row=1, column=0, sticky="W", padx=2)
        Entry(hs_lf, textvariable=self.UI_settings['HS:VIB'], width=7).grid(row=1, column=1, sticky="W", padx=2)
        Entry(hs_lf, textvariable=self.UI_settings['HS:AUD'], width=7).grid(row=1, column=2, sticky="W", padx=2)

        # Salience Definitions
        sd_lf = LabelFrame(win, text="High Low Salience Definitions (%)")
        sd_lf.pack(expand=True, fill=BOTH, pady=5, padx=3)
        sd_lf.grid_columnconfigure(0, weight=1)

        Label(sd_lf, text="LOW").grid(row=0, column=1)
        Label(sd_lf, text="HIGH").grid(row=0, column=2)

        Label(sd_lf, text="LED - Light").grid(row=1, column=0, sticky='W')
        Label(sd_lf, text="VIB - Vibration").grid(row=2, column=0, sticky='W')
        Label(sd_lf, text="AUD - Sound").grid(row=3, column=0, sticky='W')

        Entry(sd_lf, textvariable=self.UI_settings['LED:L'], width=7).grid(row=1, column=1, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self.UI_settings['LED:H'], width=7).grid(row=1, column=2, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self.UI_settings['VIB:L'], width=7).grid(row=2, column=1, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self.UI_settings['VIB:H'], width=7).grid(row=2, column=2, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self.UI_settings['AUD:L'], width=7).grid(row=3, column=1, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self.UI_settings['AUD:H'], width=7).grid(row=3, column=2, sticky='W', padx=2, pady=2)

        # Standard drt parameters
        drt_lf = LabelFrame(win, text="drt Experiment Parameters")
        drt_lf.pack(expand=True, fill=BOTH, pady=5, padx=3)
        drt_lf.grid_columnconfigure(0, weight=1)

        Label(drt_lf, text="Upper ISI (ms):").grid(row=0, column=0, sticky="NEWS", pady=1)
        Entry(drt_lf, textvariable=self.UI_settings['ISI:H'], width=7).grid(row=0, column=1, sticky="W", pady=1)

        # Lower Duration
        Label(drt_lf, text="Lower ISI (ms):").grid(row=1, column=0, sticky="NEWS", pady=1)
        Entry(drt_lf, textvariable=self.UI_settings['ISI:L'], width=7).grid(row=1, column=1, sticky="W", pady=1)

        # Stimulus Duration Duration
        Label(drt_lf, text="Stimulus Duration (ms):").grid(row=2, column=0, sticky="NEWS", pady=1)
        Entry(drt_lf, textvariable=self.UI_settings['STM:DUR'], width=7).grid(row=2, column=1, sticky="W", pady=1)

        # Upload
        button_upload = Button(win, text="Upload Configuration", command=self._upload_clicked)
        button_upload.pack(expand=True, fill=BOTH, pady=5, padx=3)

    @staticmethod
    def _filter_entry(val, default_value,  lower, upper):
        if val.isnumeric():
            val = int(val)
            if val < lower or val > upper:
                val = default_value
        else:
            return default_value
        return val

    def _clear_fields(self):
        for i in self.UI_settings:
            self.UI_settings[i].set("")

    def parse_config(self, vals):
        vals = vals.split(",")
        for kv in vals:
            kv = kv.split("=")
            if len(kv) == 2:
                key = kv[0].strip('"').strip()
                val = kv[1].strip('"').strip()
                fnc = self.UI_settings.get(key, None)
                if fnc:
                    fnc.set(val)
                    self.HW_settings[key] = val
                else:
                    print(f'{key}, {len(key)}')

    def _send_changed_parameters(self):
        for k in self.UI_settings:
            if int(self.UI_settings[k].get()) != int(self.HW_settings[k]):
                self._q_out.put(f'hi_sft>{k},{self.UI_settings[k].get()}>{self._active_tab}')
                sleep(.2)

    # Custom upload
    def _upload_clicked(self):
        self._send_changed_parameters()
        self._clear_fields()
        self._q_out.put(f'hi_sft>config>{self._active_tab}')


