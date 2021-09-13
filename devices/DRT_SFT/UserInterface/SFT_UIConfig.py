from tkinter.ttk import LabelFrame, Label, Button, Entry
from tkinter import Toplevel, StringVar, messagebox, BOTH
from queue import SimpleQueue
from math import ceil
from PIL import Image, ImageTk
from os import path


class SFTConfigWin:
    def __init__(self, to_ctrl: SimpleQueue):
        self._wDRT2c = to_ctrl
        self._var = {'HMS:0': StringVar(),
                     'HMS:1': StringVar(),
                     'HMS:2': StringVar(),
                     'HMS:3': StringVar(),

                     'WS:LED': StringVar(),
                     'WS:VIB': StringVar(),
                     'WS:AUD': StringVar(),

                     'HS:LED': StringVar(),
                     'HS:VIB': StringVar(),
                     'HS:AUD': StringVar(),

                     'LED:L': StringVar(),
                     'LED:H': StringVar(),
                     'VIB:L': StringVar(),
                     'VIB:H': StringVar(),
                     'AUD:L': StringVar(),
                     'AUD:H': StringVar(),

                     "ISI:L": StringVar(),
                     "ISI:H": StringVar(),
                     "STM:DUR": StringVar()
                     }
        self.com = None
        self.uid = None

        # Callbacks
        self._iso_cb = None
        self._custom_cb = None

    def show(self, uid):
        self.uid = uid

        win = Toplevel()
        win.grab_set()
        win.title("")
        icon_path = path.abspath(path.join(path.dirname(__file__), '../../../img/rs_icon.ico'))
        win.iconbitmap(icon_path)
        win.focus_force()
        win.resizable(False, False)
        win.grid_columnconfigure(0, weight=1)


        # How Many Stimuli
        hms_lf = LabelFrame(win, text="Count Probabilities")
        hms_lf.pack(padx=3)

        Label(hms_lf, text='HMS:0').grid(row=0, column=0)
        Label(hms_lf, text='HMS:1').grid(row=0, column=1)
        Label(hms_lf, text='HMS:2').grid(row=0, column=2)
        Label(hms_lf, text='HMS:3').grid(row=0, column=3)

        Entry(hms_lf, textvariable=self._var['HMS:0'], width=7).grid(row=1, column=0, sticky="W", padx=2)
        Entry(hms_lf, textvariable=self._var['HMS:1'], width=7).grid(row=1, column=1, sticky="W", padx=2)
        Entry(hms_lf, textvariable=self._var['HMS:2'], width=7).grid(row=1, column=2, sticky="W", padx=2)
        Entry(hms_lf, textvariable=self._var['HMS:3'], width=7).grid(row=1, column=3, sticky="W", padx=2)

        # Which Stimuli
        ws_lf = LabelFrame(win, text="Selection Probabilities")
        ws_lf.pack(expand=True, fill=BOTH, pady=5, padx=3)

        Label(ws_lf, text="WS:LED").grid(row=0, column=0)
        Label(ws_lf, text="WS:VIB").grid(row=0, column=1)
        Label(ws_lf, text="WS:AUD").grid(row=0, column=2)

        Entry(ws_lf, textvariable=self._var['WS:LED'], width=7).grid(row=1, column=0, sticky="W", padx=2)
        Entry(ws_lf, textvariable=self._var['WS:VIB'], width=7).grid(row=1, column=1, sticky="W", padx=2)
        Entry(ws_lf, textvariable=self._var['WS:AUD'], width=7).grid(row=1, column=2, sticky="W", padx=2)

        # How Salient
        hs_lf = LabelFrame(win, text="Salience Probabilities")
        hs_lf.pack(expand=True, fill=BOTH, pady=5, padx=3)

        Label(hs_lf, text="HS:LED").grid(row=0, column=0)
        Label(hs_lf, text="HS:VIB").grid(row=0, column=1)
        Label(hs_lf, text="HS:AUD").grid(row=0, column=2)

        Entry(hs_lf, textvariable=self._var['HS:LED'], width=7).grid(row=1, column=0, sticky="W", padx=2)
        Entry(hs_lf, textvariable=self._var['HS:VIB'], width=7).grid(row=1, column=1, sticky="W", padx=2)
        Entry(hs_lf, textvariable=self._var['HS:AUD'], width=7).grid(row=1, column=2, sticky="W", padx=2)

        # Salience Definitions
        sd_lf = LabelFrame(win, text="High / Low Salience Percentages")
        sd_lf.pack(expand=True, fill=BOTH, pady=5, padx=3)
        sd_lf.grid_columnconfigure(0, weight=1)

        Label(sd_lf, text="LOW").grid(row=0, column=1)
        Label(sd_lf, text="HIGH").grid(row=0, column=2)

        Label(sd_lf, text="LED - Light").grid(row=1, column=0, sticky='W')
        Label(sd_lf, text="VIB - Vibration").grid(row=2, column=0, sticky='W')
        Label(sd_lf, text="AUD - Sound").grid(row=3, column=0, sticky='W')

        Entry(sd_lf, textvariable=self._var['LED:L'], width=7).grid(row=1, column=1, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self._var['LED:H'], width=7).grid(row=1, column=2, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self._var['VIB:L'], width=7).grid(row=2, column=1, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self._var['VIB:H'], width=7).grid(row=2, column=2, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self._var['AUD:L'], width=7).grid(row=3, column=1, sticky='W', padx=2, pady=2)
        Entry(sd_lf, textvariable=self._var['AUD:H'], width=7).grid(row=3, column=2, sticky='W', padx=2, pady=2)

        # Standard DRT parameters
        drt_lf = LabelFrame(win, text="DRT Experiment Parameters")
        drt_lf.pack(expand=True, fill=BOTH, pady=5, padx=3)
        drt_lf.grid_columnconfigure(0, weight=1)

        Label(drt_lf, text="Upper ISI (ms):").grid(row=0, column=0, sticky="NEWS", pady=1)
        Entry(drt_lf, textvariable=self._var['ISI:H'], width=7).grid(row=0, column=1, sticky="W", pady=1)

        # Lower Duration
        Label(drt_lf, text="Lower ISI (ms):").grid(row=1, column=0, sticky="NEWS", pady=1)
        Entry(drt_lf, textvariable=self._var['ISI:L'], width=7).grid(row=1, column=1, sticky="W", pady=1)

        # Stimulus Duration Duration
        Label(drt_lf, text="Stimulus Duration (ms):").grid(row=2, column=0, sticky="NEWS", pady=1)
        Entry(drt_lf, textvariable=self._var['STM:DUR'], width=7).grid(row=2, column=1, sticky="W", pady=1)

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
        for i in self._var:
            self._var[i].set("")

    def parse_config(self, vals):
        vals = vals[0].strip('{').strip('}')
        vals = vals.split(",")
        for kv in vals:
            kv = kv.split("=")
            if len(kv) == 2:
                key = kv[0].strip('"').strip()
                val = float(kv[1].strip('"').strip())
                fnc = self._var.get(key, None)
                if fnc:
                    fnc.set(val)
                else:
                    print(f'{key}, {len(key)}')

    # Custom upload
    def _upload_clicked(self):
        low = self._filter_entry(self._var['lowerISI'].get(), 3000, 0, 65535)
        high = self._filter_entry(self._var['upperISI'].get(), 5000, low, 65535)
        intensity = ceil(self._filter_entry(self._var['intensity'].get(), 100, 0, 100))
        duration = self._filter_entry(self._var['stimDur'].get(), 1000, 0, 65535)

        msg = f"ONTM:{duration},ISIL:{low},ISIH:{high},DBNC:{100},SPCT:{intensity}"

        self._clear_fields()
        self._custom_cb(msg)

    def register_upload_cb(self, cb):
        self._custom_cb = cb


