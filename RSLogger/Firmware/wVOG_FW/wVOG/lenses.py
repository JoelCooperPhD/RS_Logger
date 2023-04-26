import pyb
import time

class Lenses:
    LENS_A = 'A'
    LENS_B = 'B'
    
    def __init__(self):
        # Lens controls
        self._lens_a = pyb.Pin(pyb.Pin.board.X9, pyb.Pin.OUT, value=0)
        self._lens_b = pyb.Pin(pyb.Pin.board.X10, pyb.Pin.OUT, value=0)

        # Transformer controls for legs 1 and 2
        self._flip_flop = True
        self._pwm_vals = {True: 100.0, False: 0.0}

        tim = pyb.Timer(3, freq=1000)
        self._toggle_1 = tim.channel(1, pyb.Timer.PWM, pin=pyb.Pin('Y3'))
        self._toggle_1.pulse_width_percent(self._pwm_vals[False])

        tim = pyb.Timer(3, freq=1000)
        self._toggle_2 = tim.channel(2, pyb.Timer.PWM, pin=pyb.Pin('Y4'))
        self._toggle_2.pulse_width_percent(self._pwm_vals[True])

        # Transformer toggle timer - toggles each leg at a set interval
        self._toggle_timer = pyb.Timer(4, freq=120)
        self._toggle_timer.callback(self._toggle_xformer)

    def _toggle_xformer(self, tmr):
        """
        Timer-based callback from timer 4.
        Toggles transformer legs.
        """
        self._toggle_1.pulse_width_percent(self._pwm_vals[self._flip_flop])
        self._toggle_2.pulse_width_percent(self._pwm_vals[not self._flip_flop])
        self._flip_flop = not self._flip_flop

    @property
    def on_opacity(self):
        """Lens opacity when switched on via "clear" method."""
        return self._pwm_vals[True]

    @on_opacity.setter
    def on_opacity(self, val):
        if val > 100:
            val = 100
        self._pwm_vals[True] = val

    @property
    def off_opacity(self):
        """Lens opacity when switched off via "opaque" method."""
        return self._pwm_vals[False]

    @off_opacity.setter
    def off_opacity(self, val):
        if val < 0:
            val = 0
        self._pwm_vals[False] = val

    def clear(self, lenses=[LENS_A, LENS_B]):
        """
        Set lenses to clear state.
        :param lenses: List of lenses to set to clear state. Default is [LENS_A, LENS_B].
        :return: True
        """
        if self.LENS_A in lenses:
            self._lens_a.value(1)
        if self.LENS_B in lenses:
            self._lens_b.value(1)
        return True

    def opaque(self, lenses=[LENS_A, LENS_B]):
        """
        Set lenses to opaque state.
        :param lenses: List of lenses to set to opaque state. Default is [LENS_A, LENS_B].
        :return: False
        """
        self._toggle_timer.callback(None)

        if self.LENS_A in lenses:
            self._lens_a.value(0)
        if self.LENS_B in lenses:
            self._lens_b.value(0)

        self._toggle_timer.callback(self._toggle_xformer)
        return False

# Create an instance of the Lenses class
lenses = Lenses()

# Clear and opaque methods usage
lenses.clear()
lenses.opaque()