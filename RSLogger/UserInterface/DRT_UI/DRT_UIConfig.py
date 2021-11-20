from tkinter.ttk import LabelFrame, Label, Button,  Separator, Entry
from tkinter import Toplevel, StringVar
from queue import SimpleQueue
from math import ceil
from os import path


class DRTConfigWin:
    def __init__(self, q_out: SimpleQueue):
        self._to_drt_c = q_out
        self.UI_settings = {"name": StringVar(), "lowerISI": StringVar(),
                    "upperISI": StringVar(), "stimDur": StringVar(),
                    "intensity": StringVar()}
        self._active_tab = None

    def show(self, uid):
        self._active_tab = uid

        win = Toplevel()
        win.withdraw()

        win.grab_set()
        win.title("")


        path_to_icon = path.abspath(path.join(path.dirname(__file__), '../../../rs_icon.ico'))
        win.iconbitmap(path_to_icon)

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
        Entry(lf, textvariable=self.UI_settings['upperISI'], width=7).grid(row=2, column=2, sticky="W")

        # Close Duration
        Label(lf, text="Lower ISI (ms):").grid(row=3, column=0, sticky="NEWS")
        Entry(lf, textvariable=self.UI_settings['lowerISI'], width=7).grid(row=3, column=2, sticky="W")

        # Stimulus Duration Duration
        Label(lf, text="Stimulus Duration (ms):").grid(row=4, column=0, sticky="NEWS")
        Entry(lf, textvariable=self.UI_settings['stimDur'], width=7).grid(row=4, column=2, sticky="W")

        # Stimulus Intensity
        Label(lf, text="Stimulus Intensity (%):").grid(row=5, column=0, sticky="NEWS")
        Entry(lf, textvariable=self.UI_settings['intensity'], width=7).grid(row=5, column=2, sticky="W")

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

        win.after(0, win.deiconify)

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
        low = self._filter_entry(self.UI_settings['lowerISI'].get(), 3000, 0, 65535)
        self._to_drt_c.put(f"hi_drt>set_lowerISI {low}>{self._active_tab}")

        high = self._filter_entry(self.UI_settings['upperISI'].get(), 5000, low, 65535)
        self._to_drt_c.put(f"hi_drt>set_upperISI {high}>{self._active_tab}")

        intensity = ceil(self._filter_entry(self.UI_settings['intensity'].get(), 100, 0, 100) * 2.55)
        self._to_drt_c.put(f"hi_drt>set_intensity {intensity}>{self._active_tab}")

        duration = self._filter_entry(self.UI_settings['stimDur'].get(), 1000, 0, 65535)
        self._to_drt_c.put(f"hi_drt>set_stimDur {duration}>{self._active_tab}")

        self._clear_settings()

    def _set_iso_cb(self):
        self._to_drt_c.put(f"hi_drt>iso>{self._active_tab}")
        self._clear_settings()

    def _clear_settings(self):
        for i in self.UI_settings:
            self.UI_settings[i].set("")

    def update_fields(self, msg):
        msg = msg.strip("cfg>")
        msg = msg.split(",")
        for i in msg:
            kv = i.split(":")
            k_new = kv[0].strip()
            for k in self.UI_settings:
                if k == k_new:
                    if k == "intensity":
                        self.UI_settings[k].set(str(int(int(kv[1]) / 2.55)))
                    else:
                        self.UI_settings[k].set(kv[1])
