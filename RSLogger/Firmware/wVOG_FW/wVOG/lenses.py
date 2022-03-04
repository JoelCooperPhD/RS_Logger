import pyb
import time


class Lenses:
    def __init__(self):
        # Lens controls
        self._lens_a = pyb.Pin(pyb.Pin.board.X9, pyb.Pin.OUT, value=0)
        self._lens_b = pyb.Pin(pyb.Pin.board.X10, pyb.Pin.OUT, value=0)

        # Transformer controls for legs 1 and 2
        self._flip_flop = True
        self._pwm_vals = [0.0, 100.0]
        self._pwm_vals[self._flip_flop]

        tim = pyb.Timer(3, freq=1000)
        self._toggle_1 = tim.channel(1, pyb.Timer.PWM, pin=pyb.Pin('Y3'))
        self._toggle_1.pulse_width_percent(self._pwm_vals[0])

        tim = pyb.Timer(3, freq=1000)
        self._toggle_2 = tim.channel(2, pyb.Timer.PWM, pin=pyb.Pin('Y4'))
        self._toggle_2.pulse_width_percent(self._pwm_vals[1])

        # Transformer toggle timer - toggles each leg at a set interval
        self._toggle_timer = pyb.Timer(4, freq=120)
        self._toggle_timer.callback(self._toggle_xformer)

    def _toggle_xformer(self, tmr):
        # This is a timer based callback from timer 4
        self._toggle_1.pulse_width_percent(self._pwm_vals[self._flip_flop])
        self._toggle_2.pulse_width_percent(self._pwm_vals[not self._flip_flop])
        self._flip_flop = not self._flip_flop

    # Lens opacity when switch on via "clear" method
    @property
    def on_opacity(self):
        return self._pwm_vals[1]

    @on_opacity.setter
    def on_opacity(self, val):
        if val > 100:
            val = 100
        self._pwm_vals[1] = val

    # Lens opacity when switch off via "opaque" method
    @property
    def off_opacity(self):
        return self._pwm_vals[0]

    @off_opacity.setter
    def off_opacity(self, val):
        if val < 0:
            val = 0
        self._pwm_vals[0] = val

    ###################################################
    # Lens control
    def clear(self, lenses=['a', 'b']):
        if 'a' in lenses:
            self._lens_a.value(1)
        if 'b' in lenses:
            self._lens_b.value(1)
        return time.ticks_ms()

    def opaque(self, lenses=['a', 'b']):
        self._toggle_timer.callback(None)

        if 'a' in lenses:
            self._lens_a.value(0)
        if 'b' in lenses:
            self._lens_b.value(0)

        self._toggle_timer.callback(self._toggle_xformer)
        return time.ticks_ms()


