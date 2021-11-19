from utime import ticks_us, ticks_ms, ticks_diff
from micropython import schedule
from pyb import Pin


class DebouncedSwitch:
    def __init__(self, pin="X11"):

        self._closure_us = 0
        self._first_closure = True
        self._prior_closure_us = 0  # The last closure - used for debouncing

        # Pin Config
        self._pin = Pin(pin, mode=Pin.IN, pull=Pin.PULL_UP)
        self._pin.irq(trigger=Pin.IRQ_FALLING, handler=self._resp_down_irq)

        # Properties
        self._debounce_ms = 350
        self._debounce_type = "prompt"
        self._closure_cnt = 0

        # Callbacks
        self._closure_1_cb = None
        self._click_cb = None

    # Debouncer type, only 'prompt' is currently supported
    @property
    def debounce_type(self):
        return self._debounce_type

    @debounce_type.setter
    def debounce_type(self, db_type):
        if db_type in ["prompt"]:
            self._debounce_type = db_type
        else:
            print("Only the 'prompt' algorithms is currently available")

    # Debounced Milliseconds - switch close lockout period
    @property
    def debounce_ms(self):
        return self._debounce_ms

    @debounce_ms.setter
    def debounce_ms(self, val):
        if val < 0:
            val = 0
        self._debounce_ms = val

    # Closure count
    @property
    def closure_cnt(self):
        return self._closure_cnt

    @closure_cnt.setter
    def closure_cnt(self, val):
        self._closure_cnt = val

    ##################
    # Private Methods
    def _resp_down_irq(self, e):
        self._closure_us = ticks_us()
        if self._first_closure:
            self._first_closure = False
            if self._closure_1_cb:
                schedule(self._closure_1_cb, self._closure_us)
        schedule(self._update, 0)

    def _debounced(self):
        db_type = self.debounce_type
        if db_type is "prompt":
            return self._instant()
        '''
        elif db_type is "stable":
            return self._stable()
        elif db_type is "lock-out":
            return self._lockout()
        '''

    def _instant(self):
        diff = ticks_diff(self._closure_us, self._prior_closure_us) // 1000
        db = diff > self.debounce_ms
        self._prior_closure_us = self._closure_us
        return db

    '''
    def _stable(self):
        db = True
        return db

    def _lockout(self):
        db = True
        return db
    '''

    # Called from the irq using micropython.schedule
    def _update(self, arg):
        if self._debounced():
            self.closure_cnt += 1
            if self._click_cb:
                self._click_cb()

    ##################
    # Public Methods
    def reset(self):
        self._first_closure = True
        self.closure_cnt = 0

    def value(self):
        return self._pin.value()

    def set_closure_1_callback(self, callback):
        self._closure_1_cb = callback

    def set_click_cnt_callback(self, callback):
        self._click_cb = callback