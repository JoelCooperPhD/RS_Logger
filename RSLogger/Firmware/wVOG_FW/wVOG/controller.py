import uasyncio as asyncio
from wVOG import xb, config, lenses, battery, mmc, experiments, timers
from pyb import RTC, USB_VCP, Pin, LED
from time import time, sleep

cfg_template = {"clr": "100", "cls": "1500", "dbc": "20", "srt": "1", "opn": "1500", "dta": "0", "drk": "0", "typ": "cycle"}

class WirelessVOG:
    def __init__(self, serial):
        self.serial = serial
        self.lenses = lenses.Lenses()
        self.battery = battery.LipoReader()
        self.xb = xb.XB()
        self.xb.register_incoming_message_cb(self.handle_xb_msg)
        self.mmc = mmc.MMC(self.delayed_broadcast)
        self.rtc = RTC()
        self.utc = None
        self.cfg = config.Configurator('wVOG/config.jsn')
        self.verify_cfg()
        self.exp = experiments.VOG(self.cfg.config, self.send_results, self.update_lens, self.broadcast)

    def handle_xb_msg(self, msg):
        self.parse_cmd(msg)

    def parse_cmd(self, msg):
        if ">" in msg:
            cmd, val = msg.split(">")
        else:
            cmd, val = msg, ''

        # Lenses: a, b, or x = both
        if cmd in ['a', 'b', 'x']:
            self.update_lens(cmd, val)

        # Experiment / Trial
        elif cmd == 'exp':
            self.experiment(val)
        elif cmd == 'trl':
            self.trial(val)

        # Configuration
        elif cmd == 'cfg':
            self.get_full_configuration()
        elif cmd == 'set':
            self.update_config(val)

        elif cmd == 'rtc':
            self.update_rtc(val)
        elif cmd == 'bat':
            self.get_battery()

        else:
            self.broadcast("Unknown command")

    #### Config
    def get_full_configuration(self):
        # cfg
        cfg_str = self.cfg.get_config_str()
        self.broadcast(f'cfg>{cfg_str}')

    def update_config(self, val):
        # opn: ms lenses in open or clear state
        # cls: ms lenses in closed or opaque state
        # dbc: ms switch debounce
        # typ: type of experiment. Options are 'cycle', 'peek', 'eblind', 'direct'
        # dta:
        # srt:
        # drk: opacity value between 0-100 when opaque
        # clr: opacity value between 0-100 when clear

        # Create a dictionary to store the configuration data
        self.config = {
            "clr": 100,
            "cls": 1500,
            "dbc": 20,
            "srt": 1,
            "opn": 1500,
            "dta": 0,
            "drk": 0,
            "typ": "cycle",
        }

        # Update the configuration data with the new value
        self.config[cmd] = val

    #### Lenses
    def update_lens(self, lens, state, broadcast = True):
        # x:1 -> lenses clear
        # x:0 -> lenses opaque
        # a:1, b:1 -> a or b clear
        # a:0, b:0 -> a or b opaque
        if broadcast:
            self.broadcast(f'{lens}>{str(int(state))}')
        if int(state):
            if lens == 'x':
                self.lenses.clear()
            elif lens in ['a', 'b']:
                self.lenses.clear(lens)