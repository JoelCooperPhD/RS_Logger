import uasyncio as asyncio
from pyb import Timer, Pin, LED, ADC, UART, RTC

# Custom Libs
from wDRT import battery, xbee, switch, config, mmc, drt

# Custom Libs
from wDRT import battery, xbee, switch, config, mmc, drt


class wDRT:
    def __init__(self, serial):
        self.events = {
            'get_cfg': self.get_cfg,
            'set_cfg': self.set_cfg,

            'set_iso': self.set_iso,
            'set_stm': self.set_stm,

            'dta_rcd': self.dta_rcd,
            'dta_pse': self.dta_pse,

            'get_bat': self.get_bat,
            'get_rtc': self.get_rtc,
            'set_rtc': self.set_rtc,

            'set_vrb': self.set_verbose,
        }
        # Serial
        self.serial = serial

        # Debug
        self.debug = False

        # Experiment
        self.verbose = True

        # Config
        self.cn = config.Configurator('wDRT/config.jsn')

        # DRT - The standard DRT
        self.drt = drt.DRT(self.cn.config)

        # Realtime Clock
        self.rtc = RTC()
        self.utc = None

        # MMC Save - The flash module stuck to the bottom of the unit
        self.headers = "Device_Unit,,, Block_ms, Trial, Reaction Time, Responses, UTC, Battery\n"
        self.mmc = mmc.MMC()

        # Battery
        self.battery = battery.LipoReader()

        # Xbee
        self.xb = xbee.Xbee(self.debug)

    # Asyncio Runner
    async def update(self):
        asyncio.create_task(self.button_runner())
        await asyncio.gather(
            self.xb.run(),
            self.handle_serial_msg(),
            self.handle_xb_msg(),
            self.handle_drt_msg(),
        )

    # Event Handlers
    async def handle_drt_msg(self):
        while True:
            msg_l = await self.drt.new_msg()
            while len(msg_l):
                msg = msg_l.pop(0)
                if "dta" in msg:
                    msg += ",{}\n".format(self.battery.percent())
                    self.mmc.write("wDRT_{},,,{}".format(self.xb.name_NI, msg[4:]))
                    asyncio.create_task(self.xb.transmit(msg))
                elif self.verbose:
                    asyncio.create_task(self.xb.transmit(msg))

    async def handle_serial_msg(self):
        while True:
            if self.serial.any():
                cmd = self.serial.read()
                cmd = cmd.strip().decode('utf-8')
                self.parse_cmd(cmd)
            await asyncio.sleep(0)

    async def handle_xb_msg(self):
        while True:
            cmd = await self.xb.new_cmd()
            self.parse_cmd(cmd)

    def parse_cmd(self, cmd):
        if ">" in cmd:
            kv = cmd.split(">")
            if len(kv[1]):
                self.events.get(kv[0], lambda: print("Invalid CB"))(kv[1])
            else:
                self.events.get(kv[0], lambda: print("Invalid CB"))()

    # Config File
    def get_cfg(self):
        msg = f"cfg>{self.cn.get_config_str()}"
        asyncio.create_task(self.xb.transmit(msg))

    def set_cfg(self, arg):
        self.cn.update(arg)
        self.get_cfg()

    def set_iso(self):
        self.cn.update({'ONTM': 1000, 'ISIL': 3000, 'ISIH': 5000, 'DBNC': 100, 'SPCT': 100})
        self.get_cfg()

    # Experiment
    def dta_rcd(self):
        self.mmc.init(self.headers)
        asyncio.create_task(self.drt.start())

    def dta_pse(self):
        self.drt.stop()

    def set_verbose(self, arg):
        self.verbose = True if arg == '1' else False

    # Stimulus
    def set_stm(self, arg):
        self.drt.stm.turn_on() if arg == '1' else self.drt.stm.turn_off()

    # Time
    def set_rtc(self, dt: str):
        rtc_tuple = tuple([int(i) for i in dt.split(',')])
        self.rtc.datetime(rtc_tuple)

        if self.debug:
            self.get_rtc()

    def get_rtc(self):
        r = self.rtc.datetime()
        msg = "rtc>" + ','.join([str(v) for v in r])
        asyncio.create_task(self.xb.transmit(msg))

    # Battery
    def get_bat(self):
        percent = self.battery.percent()
        msg = f"bty>{percent}"
        asyncio.create_task(self.xb.transmit(msg))

    # Button Runner - execute drt.start and drt.stop commands from button presses
    async def button_runner(self):
        down_t = 0
        while True:
            down_t = down_t + 1 if self.drt.resp.value() == 0 else 0
            if down_t == 5:
                if self.drt.running:
                    self.drt.stop()
                else:
                    self.mmc.init(self.headers)
                    asyncio.create_task(self.drt.start())
                down_t = 0
            await asyncio.sleep(1)

