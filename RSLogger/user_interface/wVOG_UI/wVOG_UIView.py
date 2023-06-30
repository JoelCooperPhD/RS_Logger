import tkinter
from tkinter.ttk import Label, LabelFrame, Button, Frame, Notebook
from tkinter import Tk, StringVar, BOTH
from RSLogger.user_interface.wVOG_UI import wVOG_UIPlotter

class wVOGTabbedControls:
    def __init__(self, win: Tk):
        self._win = win

        self._frame = Frame(win)

        self._tabs = dict()

        # Notebook - Tabs
        self.NB = Notebook(self._frame, width=160)
        self.NB.grid(row=0, column=0, sticky='NEWS')

        self.tab_f = dict()

        # Callbacks
        self._lens_a_toggle_cb = None
        self._lens_b_toggle_cb = None
        self._lens_ab_toggle_cb = None
        self._configure_clicked_cb = None
        self._rescan_network_cb = None

    ################################
    # Parent View overrides
    def build_tab(self, dev_id) -> dict:
        self.tab_f.clear()

        # Build tab
        self._tab_add_main_frame(dev_id)
        self._tab_embed_main_frame_in_nb(dev_id)
        self._tab_add_battery_bar(dev_id)
        self._tab_add_plot(dev_id)
        self._tab_add_manual_controls()
        self._tab_add_results()
        self._tab_add_configure(dev_id)

        return self.tab_f.copy()

    def _tab_add_main_frame(self, dev_id):
        self.tab_f['frame'] = Frame(self.NB, name=dev_id.lower())
        self.tab_f['frame'].grid(row=0, column=1)
        self.tab_f['frame'].grid_columnconfigure(0, weight=1)
        self.tab_f['frame'].grid_rowconfigure(3, weight=1)

    def _tab_embed_main_frame_in_nb(self, name):
        self.NB.add(self.tab_f['frame'], text=name)

    def _tab_add_battery_bar(self, id):
        if not 'COM' in id:
            lf = LabelFrame(self.tab_f['frame'], text="Battery Charge")
            lf.grid(row=0, column=1, columnspan=2, sticky="NEWS")
            lf.grid_columnconfigure(0, weight=1)

            self.tab_f['bat_f'] = Frame(lf)
            self.tab_f['bat_f'].grid(row=0, column=0, sticky="NEWS")

            for i in range(10):
                self.tab_f['bat_f'].grid_columnconfigure(i, weight=1)
                self.tab_f[f'b_{i}'] = tkinter.Label(self.tab_f['bat_f'], borderwidth=0, bg='white', relief="sunken")
                self.tab_f[f'b_{i}'].grid(row=0, column=i, sticky="NEWS", pady=2, padx=1)

    def _tab_add_plot(self, dev_id):
        self.tab_f['plot'] = wVOG_UIPlotter.Plotter(self.tab_f['frame'])
        self.tab_f['plot'].set_tsot_and_state_lines(dev_id)

    def _tab_add_manual_controls(self):
        self.tab_f['lf'] = LabelFrame(self.tab_f['frame'], text="Lens State")
        self.tab_f['lf'].grid(row=1, column=1, sticky='NEWS')
        self.tab_f['lf'].grid_columnconfigure(0, weight=1)

        self.tab_f['lf_a'] = Frame(self.tab_f['lf'])
        self.tab_f['lf_a'].grid(row=0, column=0, sticky='NEWS')

        self.tab_f['a_toggle'] = Button(self.tab_f['lf_a'], text="A Open", command=self._lens_a_toggle_cb)
        self.tab_f['a_toggle'].grid(row=0, column=0, sticky='NEWS')

        self.tab_f['b_toggle'] = Button(self.tab_f['lf_a'], text="B Open", command=self._lens_b_toggle_cb)
        self.tab_f['b_toggle'].grid(row=1, column=0, sticky='NEWS')

        self.tab_f['ab_toggle'] = Button(self.tab_f['lf'], text="AB Open", command=self._lens_ab_toggle_cb)
        self.tab_f['ab_toggle'].grid(row=0, column=1, sticky='NEWS')

    def _tab_add_results(self):
        lf = LabelFrame(self.tab_f['frame'], text="Results")
        lf.grid(row=4, column=1, sticky='NEWS')
        lf.grid_columnconfigure(1, weight=1)

        self.tab_f['trl_n'] = StringVar()
        self.tab_f['trl_n'].set("0")
        Label(lf, text="Trial Number:").grid(row=0, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['trl_n']).grid(row=0, column=1, sticky="E")

        self.tab_f['tsot'] = StringVar()
        self.tab_f['tsot'].set('0')
        Label(lf, text="Total Opened (TSOT):").grid(row=1, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['tsot']).grid(row=1, column=1, sticky="E")

        self.tab_f['tsct'] = StringVar()
        self.tab_f['tsct'].set("0")
        Label(lf, text="Total Closed (TSCT):").grid(row=2, column=0, sticky='NEWS')
        Label(lf, textvariable=self.tab_f['tsct']).grid(row=2, column=1, sticky="E")

    def _tab_add_configure(self, id):
        f = Frame(self.tab_f['frame'])
        f.grid(row=5, column=1, sticky="NEWS")
        f.grid_columnconfigure(0, weight=1)

        self.tab_f['configure'] = Button(f, text="Configure Unit", command=self._configure_clicked_cb, width=25)
        self.tab_f['configure'].grid(row=0, column=0, sticky='NEWS')

        if not 'COM' in id:
            self.tab_f['refresh'] = Button(f, text="Rescan Network", command=self._rescan_network_cb)
            self.tab_f['refresh'].grid(row=1, column=0, sticky='NEWS')


    ################################
    # Events and Callbacks
    def register_configure_clicked_cb(self, cb):
        self._configure_clicked_cb = cb

    def register_stimulus_a_toggle_cb(self, cb):
        self._lens_a_toggle_cb = cb

    def register_stimulus_b_toggle_cb(self, cb):
        self._lens_b_toggle_cb = cb

    def register_stimulus_ab_toggle_cb(self, cb):
        self._lens_ab_toggle_cb = cb

    def register_rescan_network(self, cb):
        self._rescan_network_cb = cb

    def show(self):
        self._frame.pack(fill=BOTH, expand=1)
        self._frame.columnconfigure(0, weight=1)
        self._frame.rowconfigure(0, weight=1)

    def hide(self):
        self._frame.pack_forget()



