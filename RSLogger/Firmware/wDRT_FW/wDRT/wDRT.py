import uasyncio as asyncio
from pyb import Timer, Pin, LED, ADC, UART, RTC

# Custom Libs
from wDRT import battery, xbee, switch, config, mmc, drt

# Custom Libs
from wDRT import battery, xbee, switch, config, mmc, drt


class wDRT:
    def __init__(self, serial, debug=False):
        self._debug = debug
        
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
        self.recording = False
        self.pausing = False

        # USB
        self.usb_detect = Pin('X1', mode=Pin.IN, pull=Pin.PULL_DOWN)

        # Serial
        self.serial = serial

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
        self.mmc = mmc.MMC(self.delayed_broadcast)

        # Battery
        self.battery = battery.LipoReader()

        # Xbee
        self.xb = xbee.Xbee()

    async def delayed_broadcast(self, msg):
        while not self.xb._dest_addr:
            await asyncio.sleep(.001)
        self.broadcast(msg)

    # Asyncio Runner
    async def update(self):
        asyncio.create_task(self.button_runner())
        await asyncio.gather(
            self.xb.run(),
            self.handle_serial_msg(),
            self.handle_drt_msg(),
            self.handle_xb_msg(),
        )

    # Event Handlers
    async def handle_drt_msg(self):
        while True:
            msg_l = await self.drt.new_msg()
            while len(msg_l):
                msg = msg_l.pop(0)
                if "dta" in msg:
                    msg += ",{}".format(self.battery.percent())
                    if self.mmc.present:
                        self.mmc.write("{},,,{}\n".format(self.xb.name_NI, msg[4:]))
                    self.broadcast(msg)
                elif self.verbose:
                    self.broadcast(msg)

    async def handle_serial_msg(self):
        while True:
            try:
                if self.serial.any():
                    cmd = self.serial.read()
                    cmd = cmd.strip().decode('utf-8')
                    self.parse_cmd(cmd)
            except:
                pass
            await asyncio.sleep(0)

    async def handle_xb_msg(self):
        while True:
            cmd = await self.xb.new_cmd()
            self.parse_cmd(cmd)

    def parse_cmd(self, cmd):
        if self._debug: print(f"parse_cmd: {cmd}")
        if ">" in cmd:
            kv = cmd.split(">")
            
            if len(kv[1]):
                self.events.get(kv[0], lambda: print("Invalid CB"))(kv[1])
            else:
                self.events.get(kv[0], lambda: print("Invalid CB"))()

    # Config File
    def get_cfg(self):
        msg = f"cfg>{self.cn.get_config_str()}"
        self.broadcast(msg)

    def set_cfg(self, arg):
        self.cn.update(arg)
        self.get_cfg()

    def set_iso(self):
        self.cn.update({'ONTM': 1000, 'ISIL': 3000, 'ISIH': 5000, 'DBNC': 100, 'SPCT': 100})
        self.get_cfg()

    # Experiment
    def dta_rcd(self):
        if self._debug: print("wDRT.dta_rcd")
        if not self.recording:
            self.recording = True
            asyncio.create_task(self._dta_rcd())

    async def _dta_rcd(self):
        if self.mmc.present:
            self.mmc.init(self.headers)
        await asyncio.create_task(self.drt.start())
        if self._debug: print("wDRT._dta_rcd")

    def dta_pse(self):
        if self._debug: print("wDRT.dta_pse")
        if self.recording and not self.pausing:
            asyncio.create_task(self._dta_pse())

    async def _dta_pse(self):
        await asyncio.create_task(self.drt.stop())
        if self._debug: print("wDRT._dta_pse")
        self.recording = False
        self.pausing = False

    def set_verbose(self, arg):
        if self._debug: print(f"wDRT.set_verbose {arg}")
        self.verbose = True if arg == '1' else False

    # Stimulus
    def set_stm(self, arg):
        if self._debug: print(f"wDRT.set_stm: {arg}")
        self.drt.stm.turn_on() if arg == '1' else self.drt.stm.turn_off()

    # Time
    def set_rtc(self, dt: str):
        if self._debug: print(f"wDRT.set_rtc: {dt}")
        rtc_tuple = tuple([int(i) for i in dt.split(',')])
        self.rtc.datetime(rtc_tuple)

    def get_rtc(self):
        if self._debug: print(f"wDRT.get_rtc")
        r = self.rtc.datetime()
        msg = "rtc>" + ','.join([str(v) for v in r])
        self.broadcast(msg)

    # Battery
    def get_bat(self):
        if self._debug: print("wDRT.get_bat")
        percent = self.battery.percent()
        msg = f"bty>{percent}"
        self.broadcast(msg)

    # Button Runner - execute drt.start and drt.stop commands from button presses
    async def button_runner(self):
        down_t = 0
        while True:
            if self._debug: print("wDRT.button_runner")
            down_t = down_t + 1 if self.drt.resp.value() == 0 else 0
            if down_t == 5:
                if self.drt.running:
                    self.drt.stop()
                else:
                    if self.mmc.present:
                        self.mmc.init(self.headers)
                    asyncio.create_task(self.drt.start())
                down_t = 0
            await asyncio.sleep(1)

    ################################################
    def broadcast(self, msg):
        self.serial.write(str(msg) + '\n')
        asyncio.create_task(self.xb.transmit(str(msg) + '\n'))

