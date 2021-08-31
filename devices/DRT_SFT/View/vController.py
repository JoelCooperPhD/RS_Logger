from tkinter.ttk import LabelFrame, Label, Button,  Separator, Entry
from tkinter import Toplevel, StringVar
from queue import SimpleQueue
from math import ceil
from os import path

class DRTConfigWin:
    def __init__(self, to_ctrl: SimpleQueue):
        self._to_drt_c = to_ctrl
        self._var = {"name": StringVar(), "lowerISI": StringVar(),
                    "upperISI": StringVar(), "stimDur": StringVar(),
                    "intensity": StringVar()}
        self.com = None

    def show(self, com):
        self.com = com

        win = Toplevel()
        win.grab_set()
        win.title(com)

        icon_path = path.abspath(path.join(path.dirname(__file__), '../../../img/rs_icon.ico'))
        win.iconbitmap(icon_path)

        win.focus_force()
        win.resizable(False, False)

        lf = LabelFrame(win, text="Configuration")
        lf.grid(row=0, column=0, sticky="NEWS", pady=2, padx=2)
        lf.grid_columnconfigure(1, weight=1)

        # Current Configuration
        Label(lf, text="Name: sDRT").grid(row=0, column=0, sticky="NEWS")
        # Label(lf, textvariable=self.var['name']).grid(row=0, column=1, sticky="W", columnspan=2)

        # Separator
        Separator(lf).grid(row=1, column=0, columnspan=3, sticky="NEWS", pady=5)

        # Open Duration
        Label(lf, text="Upper ISI (ms):").grid(row=2, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._var['upperISI'], width=7).grid(row=2, column=2, sticky="W")

        # Close Duration
        Label(lf, text="Lower ISI (ms):").grid(row=3, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._var['lowerISI'], width=7).grid(row=3, column=2, sticky="W")

        # Stimulus Duration Duration
        Label(lf, text="Stimulus Duration (ms):").grid(row=4, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._var['stimDur'], width=7).grid(row=4, column=2, sticky="W")

        # Stimulus Intensity
        Label(lf, text="Stimulus Intensity (%):").grid(row=5, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._var['intensity'], width=7).grid(row=5, column=2, sticky="W")

        # Separator
        Separator(lf).grid(row=6, column=0, columnspan=3, sticky="NEWS", pady=5)

        # Upload Custom
        button_upload = Button(lf, text="Upload to Device", command=self._upload_to_device_cb)
        button_upload.grid(row=7, column=0, columnspan=3, pady=5, padx=20, sticky="NEWS")

        # -----------------------------
        # Upload Standard Configuration
        lf2 = LabelFrame(win, text="Upload Standard Configuration")
        lf2.grid(row=1, column=0, sticky="NEWS", pady=(10, 0), padx=2)
        lf2.grid_columnconfigure(0, weight=1)

        # ISO
        button_iso = Button(lf2, text="ISO", command=self._set_iso_cb)
        button_iso.grid(row=0, column=0, pady=5, padx=20, sticky="NEWS")

    @staticmethod
    def _filter_entry(val, default_value,  lower, upper):
        if val.isnumeric():
            val = int(val)
            if val < lower or val > upper:
                val = default_value
        else:
            return default_value
        return val

    def _upload_to_device_cb(self):
        low = self._filter_entry(self._var['lowerISI'].get(), 3000, 0, 65535)
        self._to_drt_c.put(f"lisi>{self.com} {low}")

        high = self._filter_entry(self._var['upperISI'].get(), 5000, low, 65535)
        self._to_drt_c.put(f"uisi>{self.com} {high}")

        intensity = ceil(self._filter_entry(self._var['intensity'].get(), 100, 0, 100) * 2.55)
        self._to_drt_c.put(f"inty>{self.com} {intensity}")

        duration = self._filter_entry(self._var['stimDur'].get(), 1000, 0, 65535)
        self._to_drt_c.put(f"dur>{self.com} {duration}")

        self._clear_settings()

    def _set_iso_cb(self):
        self._to_drt_c.put(f"iso>{self.com}")
        self._clear_settings()

    def _clear_settings(self):
        self._var['lowerISI'].set("")
        self._var['upperISI'].set("")
        self._var['intensity'].set("")
        self._var['stimDur'].set("")

    def update_fields(self, msg):
        msg = msg.strip("cfg>")
        msg = msg.split(",")
        for i in msg:
            kv = i.split(":")
            k_new = kv[0].strip()
            for k in self._var:
                if k == k_new:
                    if k == "intensity":
                        self._var[k].set(str(int(int(kv[1]) / 2.55)))
                    else:
                        self._var[k].set(kv[1])
