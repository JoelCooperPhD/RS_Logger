from tkinter.ttk import Label, LabelFrame, Button, Frame, Notebook
from tkinter import Tk, StringVar, BOTH
from RSLogger.user_interface.sDRT_UI import sDRT_UIPlotter


class DRTTabbedControls:
    def __init__(self, win: Tk):
        self._win = win

        self._frame = Frame(win)

        self._tabs = dict()

        # Notebook - Tabs
        self.NB = Notebook(self._frame, width=160)
        self.NB.grid(row=0, column=0, sticky='NEWS')

        self.tab_f = dict()

        # Callbacks
        self._stimulus_on_cb = None
        self._stimulus_off_cb = None
        self._configure_clicked_cb = None

    ################################
    # Parent View overrides
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
        self.tab_f['plot'] = sDRT_UIPlotter.Plotter(self.tab_f['frame'])
        self.tab_f['plot'].set_rt_and_state_lines(dev_id)

    def _tab_add_manual_controls(self):
        self.tab_f['lf'] = LabelFrame(self.tab_f['frame'], text="Stimulus")
        self.tab_f['lf'].grid(row=1, column=1, sticky='NEWS')
        self.tab_f['lf'].grid_columnconfigure(0, weight=1)

        # Vibration Motor Controls
        self.tab_f['stm_on'] = Button(self.tab_f['lf'], text="ON", command=self._stimulus_on_cb)
        self.tab_f['stm_on'].grid(row=0, column=0, sticky='NEWS')

        self.tab_f['stm_off'] = Button(self.tab_f['lf'], text="OFF", command=self._stimulus_off_cb)
        self.tab_f['stm_off'].grid(row=0, column=1, sticky='NEWS')

    def _tab_add_results(self):
        lf = LabelFrame(self.tab_f['frame'], text="Results")
        lf.grid(row=4, column=1, sticky='NEWS')
        lf.grid_columnconfigure(1, weight=1)

        self.tab_f['trl_n'] = StringVar()
        self.tab_f['trl_n'].set("0")
        Label(lf, text="Trial Number:").grid(row=0, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['trl_n']).grid(row=0, column=1, sticky="E")

        self.tab_f['rt'] = StringVar()
        self.tab_f['rt'].set('-1')
        Label(lf, text="Reaction Time:").grid(row=1, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['rt']).grid(row=1, column=1, sticky="E")

        self.tab_f['clicks'] = StringVar()
        self.tab_f['clicks'].set("0")
        Label(lf, text="Response Count:").grid(row=2, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['clicks']).grid(row=2, column=1, sticky="E")

    def _tab_add_configure(self):
        f = Frame(self.tab_f['frame'])
        f.grid(row=5, column=1, sticky="NEWS")
        f.grid_columnconfigure(0, weight=1)

        self.tab_f['configure'] = Button(f, text="Configure Unit", command=self._configure_clicked_cb, width=25)
        self.tab_f['configure'].grid(row=0, column=0, sticky='NEWS')

    ################################
    # Events and Callbacks
    def register_configure_clicked_cb(self, cb):
        self._configure_clicked_cb = cb

    def register_stimulus_on_cb(self, cb):
        self._stimulus_on_cb = cb

    def register_stimulus_off_cb(self, cb):
        self._stimulus_off_cb = cb

    def show(self):
        self._frame.pack(fill=BOTH, expand=1)
        self._frame.columnconfigure(0, weight=1)
        self._frame.rowconfigure(0, weight=1)

    def hide(self):
        self._frame.pack_forget()

