from tkinter.ttk import LabelFrame, Label, Button, Entry
from tkinter import Toplevel, StringVar, messagebox
from queue import SimpleQueue
from math import ceil
from PIL import Image, ImageTk
from os import path


class WDRTConfigWin:
    def __init__(self, q_out):
        self._wDRT2c = q_out
        self._var = {"name": StringVar(), "lowerISI": StringVar(),
                     "upperISI": StringVar(), "stimDur": StringVar(),
                     "debounce": StringVar(), "intensity": StringVar(),
                     "xb_DL": StringVar(), "xb_MY": StringVar()}
        self.com = None
        self.uid = None

        qmark_path = path.abspath(path.join(path.dirname(__file__), '../../../img/questionmark_15.png'))
        self._qmark_img = ImageTk.PhotoImage(Image.open(qmark_path))

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

        lf = LabelFrame(win, text="Runtime Parameters")
        lf.grid(row=0, column=0, sticky="NEWS", pady=1, padx=2)
        lf.grid_columnconfigure(1, weight=1)

        # Open Duration
        Label(lf, text="Upper ISI (ms):").grid(row=5, column=0, sticky="NEWS", pady=1)
        Entry(lf, textvariable=self._var['upperISI'], width=7).grid(row=5, column=2, sticky="W", pady=1)

        # Close Duration
        Label(lf, text="Lower ISI (ms):").grid(row=6, column=0, sticky="NEWS", pady=1)
        Entry(lf, textvariable=self._var['lowerISI'], width=7).grid(row=6, column=2, sticky="W", pady=1)

        # Stimulus Duration Duration
        Label(lf, text="Stimulus Duration (ms):").grid(row=7, column=0, sticky="NEWS", pady=1)
        Entry(lf, textvariable=self._var['stimDur'], width=7).grid(row=7, column=2, sticky="W", pady=1)

        # Stimulus Intensity
        Label(lf, text="Stimulus Intensity (%):").grid(row=8, column=0, sticky="NEWS", pady=1)
        Entry(lf, textvariable=self._var['intensity'], width=7).grid(row=8, column=2, sticky="W", pady=1)

        # Upload Custom
        button_upload = Button(lf, text="Upload Custom", command=self._custom_clicked)
        button_upload.grid(row=10, column=0, columnspan=3, pady=(4, 0), padx=2, sticky="NEWS")

        # ISO
        button_iso = Button(lf, text="Upload ISO", command=self._iso_clicked)
        button_iso.grid(row=11, column=0, columnspan=3, pady=(0, 5), padx=2, sticky="NEWS")

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
        self._var['stimDur'].set("")
        self._var['lowerISI'].set("")
        self._var['upperISI'].set("")
        self._var['debounce'].set("")
        self._var['intensity'].set("")

    def parse_config(self, vals):
        def recode_config(key):
            return {
                'ONTM': 'stimDur',
                'ISIH': 'upperISI',
                'ISIL': 'lowerISI',
                'DBNC': 'debounce',
                'SPCT': 'intensity'
            }[key]

        vals = vals.split(',')
        for kv in vals:
            try:
                kv = kv.split(":")
                if len(kv) == 2:
                    new_key = recode_config(kv[0].strip(' '))
                    fnc = self._var.get(new_key, None)
                    if fnc:
                        fnc.set(int(kv[1]))
            except:
                pass

    # Custom upload
    def _custom_clicked(self):
        low = self._filter_entry(self._var['lowerISI'].get(), 3000, 0, 65535)
        high = self._filter_entry(self._var['upperISI'].get(), 5000, low, 65535)
        intensity = ceil(self._filter_entry(self._var['intensity'].get(), 100, 0, 100))
        duration = self._filter_entry(self._var['stimDur'].get(), 1000, 0, 65535)

        msg = f"ONTM:{duration},ISIL:{low},ISIH:{high},DBNC:{100},SPCT:{intensity}"

        self._clear_fields()
        self._custom_cb(msg)

    def register_custom_cb(self, cb):
        self._custom_cb = cb

    # ISO upload
    def _iso_clicked(self):
        self._clear_fields()
        self._iso_cb()

    def register_iso_cb(self, cb):
        self._iso_cb = cb

