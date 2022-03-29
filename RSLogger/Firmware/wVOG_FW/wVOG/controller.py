import uasyncio as asyncio
from wVOG import xb, config, lenses, battery, mmc, experiments, timers
from pyb import RTC, USB_VCP, Pin, LED
from time import time


class WirelessVOG:
    def __init__(self, serial):
        self.serial = serial

        # Lenses
        self.lenses = lenses.Lenses()

        # Battery
        self.battery = battery.LipoReader()

        # USB
        self.usb_attached = False
        self.usb_detect = Pin('X1', mode=Pin.IN, pull=Pin.PULL_DOWN)

        # MMC Save - The flash module stuck to the bottom of the unit
        self.headers = "Device_Unit,,, Block_ms, Trial, Reaction Time, Responses, UTC, Battery\n"
        self.mmc = mmc.MMC()

        # XB
        self.xb = xb.XB()
        self.xb.register_incoming_message_cb(self.handle_xb_msg)

        # Realtime Clock
        self.rtc = RTC()
        self.utc = None

        # Config
        self.cfg = config.Configurator('wVOG/config.jsn')

        # Experiments
        self.exp_running = False
        self.exp = experiments.VOG(self.cfg.config, self.send_results)

        # Trial
        self.trial_running = False

    def update(self):
        await asyncio.gather(
            self.handle_serial_msg(),
            self.usb_attached_poller(),
        )

    ################################################
    # Listen for incoming messages
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
        if ":" in msg:
            cmd, val = msg.split(":")
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
        elif cmd in self.cfg.config.keys():
            self.update_config(cmd, val)

        elif cmd == 'rtc':
            self.update_rtc(val)
        elif cmd == 'bat':
            self.get_battery()

        else:
            self.broadcast("Unknown command")

    ################################################
    # Lenses
    def update_lens(self, lens, state):
        # x:1 -> lenses clear
        # x:0 -> lenses opaque
        # a:1, b:1 -> a or b clear
        # a:0, b:0 -> a or b opaque

        if state == '1':
            if lens == 'x':
                self.lenses.clear()
            elif lens in ['a', 'b']:
                self.lenses.clear(lens)
        elif state == '0':
            if lens == 'x':
                self.lenses.opaque()
            elif lens in ['a', 'b']:
                self.lenses.opaque(lens)

    #### Config
    def get_full_configuration(self):
        # cfg
        self.broadcast(f'cfg:{self.cfg.config}')

    def update_config(self, key, val):
        # opn: ms lenses in open or clear state
        # cls: ms lenses in closed or opaque state
        # dbc: ms switch debounce
        # typ: type of experiment. Options are 'cycle', 'peek', 'eblind', 'direct'
        # dta:
        # srt:
        # drk: opacity value between 0-100 when opaque
        # clr: opacity value between 0-100 when clear

        if val != '':
            self.cfg.update(f"{key}:{val}")
        self.broadcast(f'{key}:{self.cfg.config[key]}')

    #### RTC
    def update_rtc(self, dt):
        if dt != '':
            rtc_tuple = tuple([int(i) for i in dt.split(',')])
            self.rtc.datetime(rtc_tuple)

        r = self.rtc.datetime()
        msg = "rtc:" + ','.join([str(v) for v in r])
        self.broadcast(msg)

    #### Battery
    def get_battery(self):
        self.broadcast(f'bty:{self.battery.percent()}')

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
    # USB attached
    async def usb_attached_poller(self):
        attached_prior = False
        attached = False
        while True:
            attached = self.usb_detect.value()
            if attached and not attached_prior:
                self.attach_event()
            if not attached and attached_prior:
                self.detatch_event()
            attached_prior = attached
            await asyncio.sleep(1)

    def attach_event(self):
        self.usb_attached = True
        self.broadcast("Attached")

    def detatch_event(self):
        self.usb_attached = False
        self.broadcast("Removed")

    ################################################
    #
    def send_results(self, dta):
        xb_name = f"wVOG_{self.xb.name_NI}"
        utc = time() + 946684800
        msg = f"dta:{xb_name},{utc},{self.trl_n},{dta}"
        self.broadcast(msg)

    def broadcast(self, msg):
        self.serial.write(msg + '\n')
        asyncio.create_task(self.xb.transmit(msg + '\n'))
