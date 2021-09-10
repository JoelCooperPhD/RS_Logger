from pyb import Pin, Timer, SPI, LED
from time import sleep, sleep_ms
import uasyncio as asyncio


'''{
"LED:L": 100, - Pin definition of a what is high or low salience
"LED:H": 5000,
"VIB:L": 100
"VIB:H": 5000,
"AUD:L": 100,
"AUD:H": 5000,
}'''

class LEDVib:
    def __init__(self, pin='X9', intensity=100, timer=4, channel=3):
        self._intensity = intensity
        self._stm = Timer(timer, freq=1000).channel(channel, Timer.PWM, pin=Pin(pin))
        self._stm.pulse_width_percent(0)
        self._stm_on = False

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

    def set_on(self):
        if not self._stm_on:
            self._stm.pulse_width_percent(self._intensity)
            self._stm_on = True
            return True
        else:
            return False

    def set_off(self):
        if self._stm_on:
            self._stm.pulse_width_percent(0)
            self._stm_on = False
            return True
        else:
            return False
    
    def fade(self):
        for i in range(100, -1, -1):
            self._stm.pulse_width_percent(i)
            sleep_ms(35)

    def toggle(self):
        if self._stm_on:
            self.set_off()
        else:
            self.set_on()


class AuditoryStimulus:
    def __init__(self):
        
        # Volume
        self._cs = Pin('X5', Pin.OUT, value=1)
        self._spi = SPI(1, SPI.MASTER, baudrate=1000000, polarity=0)
        self._volume = 0
        
        # Tone
        self._tone = 100
        self._time_gen = Timer(2, freq=self._tone)
        self._tone_pin = self._time_gen.channel(1, Timer.PWM, pin=Pin('X1'))
        self._tone_pin.pulse_width_percent(0)
        self._stm_on = False
    
    @property
    def intensity(self, val):
        return self._volume
    
    @intensity.setter
    def intensity(self, val):
        self._cs.value(0)
        
        if val <=127 and val >= 0:
            self._volume = val
        elif val >= 127:
            self._volume = 127
        elif val <= 0:
            self._volume = 0
            
        self._spi.write(b'\x00')
        self._spi.write((val).to_bytes(1, 'little'))
        
        self._cs.value(1)
    
    @property
    def tone(self, val):
        return self._tone
    
    @tone.setter
    def tone(self, val):
        if val <= 20000 and val >= 20:
            self._tone = val
        elif val >= 20000:
            self._tone = 20000
        elif val <= 20:
            self._tone= 20
            
        self._time_gen = Timer(2, freq=self._tone)
        self._tone_pin.pulse_width_percent(50)
        
    def set_on(self):
        if not self._stm_on:
            self._tone_pin.pulse_width_percent(50)
            self._stm_on = True
            return True
        else:
            return False
        
    def set_off(self):
        if self._stm_on:
            self._tone_pin.pulse_width_percent(0)
            self._stm_on = False
            return True
        else:
            return False

    def toggle(self):
        if self._stm_on:
            self.set_off()
        else:
            self.set_on()

