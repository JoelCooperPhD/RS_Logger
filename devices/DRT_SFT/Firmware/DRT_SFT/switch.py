from utime import ticks_ms, ticks_ms, ticks_diff
from micropython import schedule
from pyb import Pin

import uasyncio as asyncio


class DebouncedSwitch:
    def __init__(self, pin="X11"):

        self._closure_ms = 0
        self._first_closure = True
        self._prior_closure_ms = 0  # The last closure - used for debouncing

        # Pin Config
        self._pin = Pin(pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self._pin.irq(trigger=Pin.IRQ_FALLING, handler=self._resp_down_irq)

        # Properties
        self._debounce_ms = 350
        self._closure_cnt = 0

        # Flags
        self._closure_1_flag = asyncio.ThreadSafeFlag()
        self._closure_n_flag = asyncio.ThreadSafeFlag()

        # Callbacks
        self._closure_1_cb = None
        self._click_cb = None
        
    async def update(self):
        await asyncio.gather(
            self._1st_closure(),
            self._nth_closure()
            )
    # Closure count
    @property
    def closure_cnt(self):
        return self._closure_cnt

    @closure_cnt.setter
    def closure_cnt(self, val):
        self._closure_cnt = val

    # Debounced Milliseconds - switch close lockout period
    @property
    def debounce_ms(self):
        return self._debounce_ms

    @debounce_ms.setter
    def debounce_ms(self, val):
        if val < 0:
            val = 0
        self._debounce_ms = val

    ##################
    # Private Methods
    def _resp_down_irq(self, e):
        self._closure_ms = ticks_ms()
        if self._first_closure:
            self._first_closure = False
            self._closure_1_flag.set()
                
        self._closure_n_flag.set()

    def _debounced(self):
        diff = ticks_diff(self._closure_ms, self._prior_closure_ms)
        self._prior_closure_ms = self._closure_ms
        return diff > self.debounce_ms
        
    async def _1st_closure(self):
        while True:
            await self._closure_1_flag.wait()
            if self._closure_1_cb:
                self._closure_1_cb(self._closure_ms)
        
    # Called from the irq 
    async def _nth_closure(self):
        while True:
            await self._closure_n_flag.wait()
            
            if self._debounced():
                self._closure_cnt += 1
                if self._click_cb:
                    self._click_cb()

    ##################
    # Public Methods
    def reset(self):
        self._first_closure = True
        self._closure_cnt = 0

    def set_closure_1_callback(self, callback):
        self._closure_1_cb = callback

    def set_click_cnt_callback(self, callback):
        self._click_cb = callback