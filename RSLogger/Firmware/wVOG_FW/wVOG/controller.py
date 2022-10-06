import uasyncio as asyncio
from wVOG import xb, config, lenses, battery, mmc, experiments, timers
from pyb import RTC, USB_VCP, Pin, LED
from time import time, sleep

cfg_template = {"clr": "100", "cls": "1500", "dbc": "20", "srt": "1", "opn": "1500", "dta": "0", "drk": "0", "typ": "cycle"}

class WirelessVOG:
    def __init__(self, serial):
        self.serial = serial

        # Lenses
        self.lenses = lenses.Lenses()

        # Battery
        self.battery = battery.LipoReader()
        
        # XB
        self.xb = xb.XB()
        self.xb.register_incoming_message_cb(self.handle_xb_msg)

        # MMC Save - The flash module stuck to the bottom of the unit
        self.headers = "Device_Unit,Controls Label,Host UTC,Trial,X,Total Task Time Time,Total Shutter Closed Time,Total Shutter Open Time,Battery Percent, Device UTC\n"
        self.mmc = mmc.MMC(self.delayed_broadcast)

        # Realtime Clock
        self.rtc = RTC()
        self.utc = None

        # Config
        self.cfg = config.Configurator('wVOG/config.jsn')
        self.verify_cfg()

        # Experiments
        self.exp_running = False
        self.exp = experiments.VOG(self.cfg.config, self.send_results, self.update_lens, self.broadcast)

        # Trial
        self.trial_running = False
        
        asyncio.create_task(self.handle_serial_msg())
        

    ################################################
    # Listen for incoming messages
    async def delayed_broadcast(self, msg):
        while not self.xb._dest_addr:
            await asyncio.sleep(.001)
        self.broadcast(msg)
    
    async def handle_serial_msg(self):
        while True:
            if self.serial.any():
                msg = self.serial.read()
                msg = msg.strip().decode('utf-8')
                self.parse_cmd(msg)
            await asyncio.sleep(.01)

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

    ################################################
    # Lenses
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
        else:
            if lens == 'x':
                self.lenses.opaque()
            elif lens in ['a', 'b']:
                self.lenses.opaque(lens)

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

        if val != '':
            kvs = val.split(',')
            for kv in kvs:
                self.cfg.update(kv)
            cfg_str = self.cfg.get_config_str()
            self.broadcast(f'cfg>{cfg_str}')
            
    #### RTC
    def update_rtc(self, dt):
        if dt != '':
            rtc_tuple = tuple([int(i) for i in dt.split(',')])
            self.rtc.datetime(rtc_tuple)

        r = self.rtc.datetime()
        msg = "rtc>" + ','.join([str(v) for v in r])
        self.broadcast(msg)

    #### Battery
    def get_battery(self):
        self.broadcast(f'bty>{self.battery.percent()}')

    ################################################
    # Experiment
    def experiment(self, val):
        # exp:1 -> start
        # exp:0 -> stop

        if val == '1':
            self.begin_experiment()
        elif val == '0':
            self.end_experiment()

    def begin_experiment(self):
        self.exp_running = True
        if self.mmc.mmc_present:
            self.mmc.init(self.headers)

        self.trl_n = 0
        self.exp.begin_experiment()

    def end_experiment(self):
        if self.trial_running:
            self.end_trial()
        self.exp_running = False

        self.exp.end_experiment()

    # Tial
    def trial(self, val):
        # trl:1 -> start
        # trl:0 -> stop

        if val == '1':
            self.begin_trial()
        elif val == '0':
            self.end_trial()

    def begin_trial(self):
        if not self.exp_running:
            self.begin_experiment()
        self.trial_running = True

        self.trl_n += 1
        self.exp.begin_trial()

    def end_trial(self):
        self.trial_running = False

        self.exp.end_trial()

    ################################################
    #
    def verify_cfg(self):
        if len(cfg_template) != len(self.cfg.config):
            self.cfg.update(cfg_template)
        for key in self.cfg.config:
            if self.cfg.config[key] == "":
                self.cfg.update(cfg_template)
                break

    def send_results(self, dta):
        # xb_name = f"wVOG_{self.xb.name_NI}"
        utc = time() + 946684800
        msg = f"dta>,{self.trl_n},{dta},{self.battery.percent()},{utc}"
        
        self.broadcast(msg)
        if self.mmc.mmc_present:
            self.mmc.write(f"{self.xb.name_NI},,{msg[4:]}\n")

    def broadcast(self, msg):
        asyncio.create_task(self.xb.transmit(msg + '\n'))
        self.serial.write(msg + '\n')
        
