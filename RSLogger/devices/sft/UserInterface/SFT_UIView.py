from tkinter.ttk import Label, LabelFrame, Button, Frame, Notebook
from tkinter import Tk, StringVar, BOTH
from RSLogger.devices.sft.UserInterface import SFT_UIPlotter


class SFTTabbedControls:
    def __init__(self, win: Tk):
        self._win = win

        self._frame = Frame(win)

        self._tabs = dict()

        # Notebook - Tabs
        self.NB = Notebook(self._frame)
        self.NB.grid(row=0, column=0, sticky='NEWS')

        self.tab_f = dict()

        # Toggle Controls
        # Callbacks
        self._rt_checkbox_cb = None
        self._state_checkbox_cb = None
        self._vib_l_cb = None
        self._vib_h_cb = None
        self._led_l_cb = None
        self._led_h_cb = None
        self._aud_l_cb = None
        self._aud_h_cb = None
        self._configure_clicked_cb = None

    def build_tab(self, dev_id) -> dict:
        self.tab_f.clear()

        # Build tab
        self._tab_add_main_frame(dev_id)
        self._tab_embed_main_frame_in_nb(dev_id)
        self._tab_add_plot(dev_id)
        self._tab_add_manual_controls()
        self._tab_add_results()
        self._tab_add_configure()

        return self.tab_f.copy()

    def _tab_add_main_frame(self, dev_id):
        self.tab_f['frame'] = Frame(self.NB, name=dev_id.lower())
        self.tab_f['frame'].grid(row=0, column=1)
        self.tab_f['frame'].grid_columnconfigure(0, weight=1)
        self.tab_f['frame'].grid_rowconfigure(3, weight=1)

    def _tab_embed_main_frame_in_nb(self, name):
        self.NB.add(self.tab_f['frame'], text=name)

    def _tab_add_plot(self, dev_id):
        self.tab_f['plot'] = SFT_UIPlotter.Plotter(self.tab_f['frame'])
        self.tab_f['plot'].set_rt_and_state_lines(dev_id)

    def _tab_add_manual_controls(self):
        self.tab_f['lf'] = LabelFrame(self.tab_f['frame'], text="Toggle Stimuli")
        self.tab_f['lf'].grid(row=1, column=1, sticky='NEWS')
        self.tab_f['lf'].grid_columnconfigure(0, weight=1)

        # Vibration Motor Controls
        self.tab_f['on_vib_l'] = Button(self.tab_f['lf'], text="VIB:LOW", command=self._vib_l_cb)
        self.tab_f['on_vib_l'].grid(row=0, column=0, sticky='NEWS')

        self.tab_f['on_vib_h'] = Button(self.tab_f['lf'], text="VIB:HIGH", command=self._vib_h_cb)
        self.tab_f['on_vib_h'].grid(row=0, column=1, sticky='NEWS')

        # LED controls
        self.tab_f['on_led_l'] = Button(self.tab_f['lf'], text="LED:LOW", command=self._led_l_cb)
        self.tab_f['on_led_l'].grid(row=1, column=0, sticky='NEWS')

        self.tab_f['on_led_h'] = Button(self.tab_f['lf'], text="LED:HIGH", command=self._led_h_cb)
        self.tab_f['on_led_h'].grid(row=1, column=1, sticky='NEWS')

        # Auditory controls
        self.tab_f['on_aud_l'] = Button(self.tab_f['lf'], text="AUD:LOW", command=self._aud_l_cb)
        self.tab_f['on_aud_l'].grid(row=2, column=0, sticky='NEWS')

        self.tab_f['on_aud_h'] = Button(self.tab_f['lf'], text="AUD:HIGH", command=self._aud_h_cb)
        self.tab_f['on_aud_h'].grid(row=2, column=1, sticky='NEWS')

    def _tab_add_results(self):
        lf = LabelFrame(self.tab_f['frame'], text="Results")
        lf.grid(row=4, column=1, sticky='NEWS')
        lf.grid_columnconfigure(1, weight=1)

        self.tab_f['trl_n'] = StringVar()
        self.tab_f['trl_n'].set("NA")
        Label(lf, text="Trial Number:").grid(row=0, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['trl_n']).grid(row=0, column=1, sticky="E")

        self.tab_f['rt'] = StringVar()
        self.tab_f['rt'].set("NA")
        Label(lf, text="Reaction Time:").grid(row=1, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['rt']).grid(row=1, column=1, sticky="E")

        self.tab_f['clicks'] = StringVar()
        self.tab_f['clicks'].set("NA")
        Label(lf, text="Response Count:").grid(row=2, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['clicks']).grid(row=2, column=1, sticky="E")

    def _tab_add_configure(self):
        f = Frame(self.tab_f['frame'])
        f.grid(row=5, column=1, sticky="NEWS")
        f.grid_columnconfigure(0, weight=1)

        self.tab_f['configure'] = Button(f, text="Configure Unit", command=self._configure_clicked_cb, width=25)
        self.tab_f['configure'].grid(row=0, column=0, sticky='NEWS')

    # Events and Callbacks
    def register_rt_checkbox_cb(self, cb):
        self._rt_checkbox_cb = cb

    def register_state_checkbox_cb(self, cb):
        self._state_checkbox_cb = cb

    def register_vib_l_cb(self, cb):
        self._vib_l_cb = cb

    def register_vib_h_cb(self, cb):
        self._vib_h_cb = cb

    def register_led_l_cb(self, cb):
        self._led_l_cb = cb

    def register_led_h_cb(self, cb):
        self._led_h_cb = cb

    def register_aud_l_cb(self, cb):
        self._aud_l_cb = cb

    def register_aud_h_cb(self, cb):
        self._aud_h_cb = cb

    def register_configure_clicked_cb(self, cb):
        self._configure_clicked_cb = cb

    def show(self):
        self._frame.pack(fill=BOTH, expand=1)
        self._frame.columnconfigure(0, weight=1)
        self._frame.rowconfigure(0, weight=1)

    def hide(self):
        self._frame.pack_forget()








