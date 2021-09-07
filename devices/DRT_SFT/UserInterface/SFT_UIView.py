from tkinter.ttk import LabelFrame, Label, Button, Checkbutton
from tkinter import BOTH, StringVar, IntVar, LEFT
from tkinter.ttk import Frame, Notebook

from devices.DRT_SFT.UserInterface import SFT_UIPlotter, SFT_UIConfigWindow


class SFTMainWindow:
    def __init__(self, win, q2v):
        pass


        self._win = win
        self._frame = Frame(win)
        self._frame.pack(fill=BOTH)

        # Notebook - Tabs

        self._NB = Notebook(self._frame, width=160)
        self._NB.grid(row=0, column=1, sticky='NEWS')

        self._tabs = dict()
        self._com = ""

        # Window params
        self._row = 2

        self._q2v = q2v

        # Plot Controls
        self._plot = SFT_UIPlotter.Plotter(self._frame)
        self._plot.add_rt_plot("SFT Detection Response Task", "RT-Seconds")
        self._plot.add_state_plot("Stimulus")

        # Config Window
        self._config_w = SFT_UIConfigWindow.SFTConfigWin(self._q2v)

        # Events
        self._events = {
            "init": self._log_init,
            "close": self._log_close,
            "record": self._data_record,
            "pause": self._data_pause,
            "add": self._add_tab,
            "remove": self._remove_tab,
            "show": self._show,
            "hide": self._hide,

            # Plot Commands
            "plt.rt": self._update_plot_rt,
            "plt.stim": self._update_plot_stimulus,
            "plt.clear": self._clear_plot,

            # DRT Commands
            "cfg": None,
            "trl": self._update_live_trial_n,
            "rt": self._update_live_rt,
            "clicks": self._update_live_clicks
        }
        self._event_dispatcher()

    def _event_dispatcher(self):
        while not self._q2v.empty():
            msg = self._q2v.get()
            try:
                if len(msg):
                    msg_l = msg.split(">")
                    self._events[msg_l[0]](msg)
            except KeyError:
                print(f"drtView event not handled: {msg}")
        self._win.after(10, self._event_dispatcher)

    ################################
    # Parent UserInterface overrides
    def _build_tab(self, port) -> dict:
        model = dict()

        # Tab
        model['tab'] = Frame(self._NB, name=port.lower())
        self._NB.add(model['tab'], text=port)
        self._NB.bind("<<NotebookTabChanged>>", self._tab_changed_event)

        # Lens Control
        f = LabelFrame(model['tab'], text="Stimulus Control")
        f.pack(expand=True, fill=BOTH)

        model['on'] = Button(f, text="On", command=self._stimulus_on_cb)
        model['on'].pack(side=LEFT, expand=True, fill=BOTH)

        model['off'] = Button(f, text="Off", command=self._stimulus_off_cb)
        model['off'].pack(side=LEFT, expand=True, fill=BOTH)

        # Plot controls
        lf = LabelFrame(model['tab'], text="Plot Controls")
        lf.pack(expand=True, fill=BOTH)

        model['plt_rt'] = IntVar()
        model['plt_rt'].set(1)
        model['cb_rt'] = Checkbutton(lf, text="Reaction Time", variable=model['plt_rt'],
                                     onvalue=1, offvalue=0, command=self._rt_cb)
        model['cb_rt'].grid(row=3, column=0, sticky='W')

        model['plt_stim'] = IntVar()
        model['plt_stim'].set(1)
        model['cb_stim'] = Checkbutton(lf, text="Stimulus", variable=model['plt_stim'],
                                       onvalue=1, offvalue=0, command=self._stimulus_state_cb)
        model['cb_stim'].grid(row=5, column=0, sticky="W")

        # Results
        lf = LabelFrame(model['tab'], text="Results")
        lf.pack(expand=True, fill=BOTH)

        model['trl_n'] = StringVar()
        model['trl_n'].set("NA")
        Label(lf, text="Trial Number:").grid(row=0, column=0, sticky='NEWS')
        Label(lf, textvariable=model['trl_n']).grid(row=0, column=1, sticky="E")

        model['rt'] = StringVar()
        model['rt'].set("NA")
        Label(lf, text="Reaction Time:").grid(row=1, column=0, sticky='NEWS')
        Label(lf, textvariable=model['rt']).grid(row=1, column=1, sticky="E")

        model['clicks'] = StringVar()
        model['clicks'].set("NA")
        Label(lf, text="Response Count:").grid(row=2, column=0, sticky='NEWS')
        Label(lf, textvariable=model['clicks']).grid(row=2, column=1, sticky="E")

        # Configure Button
        model['configure'] = Button(model['tab'], text="Configure", width=20, command=self._configure_clicked_cb)
        model['configure'].pack(expand=True, fill=BOTH)

        return model

    def _add_tab(self, msg):
        port = msg.split(">")[1]
        self._tabs[port] = self._build_tab(port)
        self._plot.set_rt_and_state_lines(port)

    def _remove_tab(self, msg: str):
        cmd, port = msg.split(">")
        self._NB.forget(self._NB.children[port.lower()])
        self._tabs.pop(port)
        self._plot.clear_all()
        self._plot.remove_port(port)

    def _tab_changed_event(self, e):
        try:
            self._com = self._NB.tab(self._NB.select(), 'text')
        except:
            pass

    #############################
    # Controls
    def _log_init(self, arg, _reset=True):
        pass

    def _log_close(self, arg):
        for port in self._tabs:
            self._tabs[port]['trl_n'].set("NA")
            self._tabs[port]['rt'].set("NA")
            self._tabs[port]['clicks'].set("NA")

    def _data_record(self, arg):
        self._plot.run = True
        self._plot.clear_all()
        self._plot.rt_update()

    def _data_pause(self, arg):
        self._plot.run = False

    #############################
    # Update plot lines

    def _update_plot_rt(self, msg):
        data = msg.split(">")[1]
        com = msg.split(">")[2]
        self._plot.rt_update(com, int(data))

    def _update_plot_stimulus(self, msg):
        data = msg.split(">")[1]
        com = msg.split(">")[2]
        self._plot.state_update(com, int(data))

    def _clear_plot(self, arg):
        self._plot.clear_all()

    #############################
    # Live Results
    def _update_live_trial_n(self, msg):
        trl = msg.split(">")[1]
        com = msg.split(">")[2]
        self._tabs[com]['trl_n'].set(trl)

    def _update_live_rt(self, msg):
        rt = msg.split(">")[1]
        com = msg.split(">")[2]
        self._tabs[com]['rt'].set(rt)

    def _update_live_clicks(self, msg):
        data = msg.split(">")[1]
        com = msg.split(">")[2]
        self._tabs[com]['clicks'].set(data)

    def _reset_live_results(self, msg):
        com = msg.split(">")[1]
        self._tabs[com]['trl_n'].set("NA")
        self._tabs[com]['rt'].set("NA")
        self._tabs[com]['clicks'].set("NA")

    ################################
    # UI Callbacks

    def _configure_clicked_cb(self):
        com = self._NB.tab(self._NB.select(), 'text')
        self._q2v.put(f"config>{com}")
        self._config_w.show(com)
        SFT_UIConfigWindow.SFTConfigWin(self._q2v)

    def _stimulus_on_cb(self):
        self._q2v.put(f"stm_on>{self._NB.tab(self._NB.select(), 'text')}")

    def _stimulus_off_cb(self):
        self._q2v.put(f"stm_off>{self._NB.tab(self._NB.select(), 'text')}")

    def _stimulus_state_cb(self):
        com = self._NB.tab(self._NB.select(), 'text')
        val = self._tabs[com]['plt_stim'].get()

        if val == 1:
            self._plot.show_lines(com, 'stim_state')
        else:
            self._plot.hide_lines(com, 'stim_state')

    def _rt_cb(self):
        com = self._NB.tab(self._NB.select(), 'text')
        val = self._tabs[com]['plt_rt'].get()

        if val == 1:
            self._plot.show_lines(com, 'rt')
        else:
            self._plot.hide_lines(com, 'rt')

    ################################
    # Misc functions

    def _show(self, arg):
        self._frame.pack(fill=BOTH, expand=1)
        self._frame.columnconfigure(0, weight=1)
        self._frame.rowconfigure(0, weight=1)

    def _hide(self, arg):
        self._frame.pack_forget()