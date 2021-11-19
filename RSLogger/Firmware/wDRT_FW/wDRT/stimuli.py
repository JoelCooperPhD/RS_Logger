from pyb import Timer, Pin, LED
from time import sleep_ms
import uasyncio as asyncio


class DRTStimulus:
    def __init__(self, pin='Y4', intensity=100):
        self._intensity = intensity
        self._stm = Timer(3, freq=1000).channel(2, Timer.PWM, pin=Pin(pin))
        self._stm.pulse_width_percent(0)
        self._stm_on = False
        # Onboard LED

        self._color = {'red': 1, 'green': 2, 'blue': 3}
        self._selected = 'red'
        self._LED = LED(self._color[self._selected])

    @property
    def LED_color(self):
        return self._selected

    @LED_color.setter
    def LED_color(self, color):
        if color in self._color:
            self._selected = color
            self._LED = LED(self._color[self._selected])
        else:
            print('color must be: "red", "blue", or "green"')

    @property
    def intensity(self):
        return self._intensity

    @intensity.setter
    def intensity(self, val):
        if val > 100:
            val = 100
        elif val < 0:
            val = 0
        self._intensity = val

    def turn_on(self):
        if not self._stm_on:
            self._all_on()
            self._stm_on = True
            return True
        else:
            return False

    def turn_off(self):
        if self._stm_on:
            self._all_off()
            self._stm_on = False
            return True
        else:
            return False
    
    async def fade(self):
        for i in range(100, -1, -1):
            self._stm.pulse_width_percent(i)
            await asyncio.sleep_ms(35)
    
    def pulse(self, times=6):
        for i in range(times):
            self._all_on()
            sleep_ms(125)
            self._all_off()
            sleep_ms(50)

    def _all_on(self):
        self._stm.pulse_width_percent(self._intensity)
        self._LED.on()

    def _all_off(self):
        self._stm.pulse_width_percent(0)
        self._LED.off()