import uasyncio as asyncio
from wVOG import xb, config, lenses, battery, mmc, experiments, timers
from pyb import RTC
from time import time


class WirelessVOG:
    def __init__(self, serial):
        self.serial = serial

        # Lenses
        self.lenses = lenses.Lenses()

        # Battery
        self.battery = battery.LipoReader()

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
        self.exp_peek = experiments.Peek(self.cfg.config, self.send_results)

    def update(self):
        await asyncio.gather(
            self.handle_serial_msg(),
        )

    ################################################
    # Listen for incoming messages
    async def handle_serial_msg(self):
        while True:
            if self.serial.any():
                cmd = self.serial.read()
                cmd = cmd.strip().decode('utf-8')
                self.parse_cmd(cmd)
            await asyncio.sleep(.01)

    def handle_xb_msg(self, cmd):
        self.parse_cmd(cmd)

    def parse_cmd(self, cmd):
        try:
            action, key, val = cmd.split(">")

            if action == 'do':
                self.handle_do(key, val)
            elif action == 'get':
                self.handle_get(key, val)
            elif action == 'set':
                self.handle_set(key, val)

        except ValueError:
            print("ERROR: Malformed command")

    ################################################
    # Handle Incoming Commands

    #### DO Commands
    def handle_do(self, key, val):
        if key == 'lens':
            self.update_lens_states(key, val)
        elif key == 'start':
            self.start(val)
        elif key == 'stop':
            self.stop(val)

    def update_lens_states(self, key, val):
        # 'do>lens>[open, close]:[a, b]'  :Example - 'do>lens>close:' or 'do>lens>open:a'
        key, val = val.split(":")
        lenses = ['a', 'b']
        if val in lenses: lenses = val

        if key == 'open':
            self.lenses.clear(lenses)
        elif key == 'close':
            self.lenses.opaque(lenses)

    #### GET Commands
    def handle_get(self, key, val):
        if key == 'cfg':
            self.get_config(val)
        elif key == 'bat':
            self.get_battery()
        elif key == 'rtc':
            self.get_rtc()

    def get_config(self, val):
        # Example: 'get>cfg>' or 'get>cfg>open'
        if val in self.cfg.config.keys():
            self.broadcast(f'cfg>{val}:{self.cfg.config[val]}')
        else:
            self.broadcast(f'cfg>{self.cfg.get_config_str()}')

    def get_rtc(self):
        r = self.rtc.datetime()
        msg = "rtc>" + ','.join([str(v) for v in r])
        self.broadcast(msg)

    def get_battery(self):
        self.broadcast(f'bty>{self.battery.percent()}')

    #### SET Commands - Sets configurations in the config.jsn file with the same names
    def handle_set(self, key, val):
        if key == 'cfg':
            self.set_config(val)
        elif key == 'rtc':
            self.set_rtc(val)

    def set_config(self, kv):
        # Example: 'set>cfg>open:1500'
        key, val = kv.split(":")
        # Example: 'set>open>1400' or 'set>debounce>45'
        self.cfg.update(f"{key}:{val}")
        self.broadcast(f'cfg>{key}:{self.cfg.config[key]}')

    # Time
    def set_rtc(self, dt: str):
        rtc_tuple = tuple([int(i) for i in dt.split(',')])
        self.rtc.datetime(rtc_tuple)

        if self.debug:
            self.get_rtc()

    ################################################
    # Experiments
    # Peek
    def start(self, val):
        if val == "exp":
            self.begin_experiment()
        elif val == "trl":
            self.begin_trial()

    def stop(self, val):
        if val == "exp":
            self.end_experiment()
        elif val == "trl":
            self.end_trial()

    def begin_experiment(self):
        self.trl_n = 0
        self.exp_running = True
        self.broadcast("starting exp...")

    def end_experiment(self):
        self.exp_running = False
        self.broadcast("stopping exp...")

    def begin_trial(self):
        if not self.exp_running:
            self.begin_experiment()
        self.trial_running = True
        self.trl_n += 1

        if self.cfg.config['type'] == "peek":
            self.exp_peek.begin_trial()
        elif self.cfg.config['type'] == "cycle":
            self.exp_cycle.begin_trial()
        elif self.cfg.config['type'] == "direct":
            self.exp_direct.begin_trial()

    def end_trial(self):
        self.trial_running = False

        if self.cfg.config['type'] == "peek":
            self.exp_peek.end_trial()
        elif self.cfg.config['type'] == "cycle":
            self.exp_cycle.end_trial()
        elif self.cfg.config['type'] == "direct":
            self.exp_direct.end_trial()

    ################################################
    #
    def send_results(self, dta):
        xb_name = f"wVOG_{self.xb.name_NI}"
        utc = time() + 946684800
        msg = f"dta>{xb_name},{utc},{self.trl_n},{dta}"
        self.broadcast(msg)

    def broadcast(self, msg):
        self.serial.write(msg + '\n')
        asyncio.create_task(self.xb.transmit(msg + '\n'))
