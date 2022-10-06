import uasyncio as asyncio
from time import sleep_ms
from uasyncio import Event
from wDRT.timers import Countdown, Stopwatch
from wDRT.stimuli import DRTStimulus
from wDRT.switch import DebouncedSwitch
from random import randrange
from time import time
import gc


class DRT:
    def __init__(self, cfg):
        # self._cfg = {'ONTM': 1000, 'ISIL': 3000, 'ISIH': 5000, 'DBNC': 100, 'SPCT': 100}
        self._cfg = cfg
        
        # Stimulus
        self.stm = DRTStimulus()
        self._stm_timer = Countdown(self._stim_on_dur_expired_cb, self._cfg['ONTM'])

        # Response
        self.resp = DebouncedSwitch()
        self.resp.set_closure_1_callback(self._first_response_cb)
        self.resp.set_click_cnt_callback(self._click_cnt_cb)

        # Block
        self.running = False
        self._blk_ms = Stopwatch()

        # Trial
        self._trl_timer = Countdown(self._trial_over_cb, self._new_duration())

        # Return Metrics
        self._stop_utc = time() + 946684800
        self._rt_sw = Stopwatch(precision='us')
        self._trl_n = 0

        # New Commands
        self._new_msg = Event()
        self._msg = list()

    
    async def start(self):
        if not self.running:
            self.running = True
            self.stm.pulse()
            await asyncio.sleep_ms(self._new_duration())
    
            self._stm_timer.run = True
            self._trl_timer.run = True
            asyncio.create_task(self._run_block())
            self._rt_sw.stop()
            self._msg.append("stm>0")

    def stop(self):
        self.running = False
        self._stm_timer.run = False
        self._trl_timer.run = False
        # sleep_ms(100)
        asyncio.create_task(self.stm.fade())

    async def _run_block(self):
        self._trl_n = 0
        self._blk_ms.start()
        while self.running:
            await asyncio.create_task(self._run_trial())
        self.stm.turn_off()

    async def _run_trial(self):
        # Initialize
        self.resp.reset()
        self._rt = -1
        self._trl_n += 1
        duration = self._new_duration()

        # Begin
        self._rt_sw.start()
        self.stm.turn_on()
        
        self._msg.append("stm>1")
        self._new_msg.set()

        await asyncio.gather(
            asyncio.create_task(self._stm_timer.start()),
            asyncio.create_task(self._trl_timer.start(duration)),
        )

    def _first_response_cb(self, e):
        self._rt = self._rt_sw.stop(e)

        if self.stm.turn_off():
            self._msg.append("stm>0")
        self._msg.append("rt>{}".format(self._rt))
        self._new_msg.set()
        
    def _click_cnt_cb(self):
        self._msg.append("clk>{}".format(self.resp.closure_cnt))
        self._new_msg.set()

    def _stim_on_dur_expired_cb(self, e):
        if self.stm.turn_off():
            self._msg.append("stm>0")
            self._new_msg.set()

    def _trial_over_cb(self, blk_run_ms):
        self._stop_utc = time() + 946684800
        self._msg.append("dta>{},{},{},{},{}".format(self._blk_ms.read(), self._trl_n, self._rt, self.resp.closure_cnt, self._stop_utc))
        self._memory_check()
        self._new_msg.set()
        
    def _memory_check(self):
        if gc.mem_free() < 20_000:
            gc.collect()

    def _new_duration(self):
        return randrange(self._cfg['ISIL'], self._cfg['ISIH'])

    async def new_msg(self):
        while True:
            await self._new_msg.wait()
            self._new_msg.clear()

            return self._msg

