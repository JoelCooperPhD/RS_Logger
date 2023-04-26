from pyb import ADC, Pin
from micropython import const
from array import array
import uasyncio as asyncio
from time import ticks_ms, ticks_diff


class LipoReader:
    def __init__(self, pin='X8'):
        self._bat_pin = ADC(Pin(pin))

        self._vref = 3.3
        self._vcut = 3.3
        self._vmax = 4.00
        self._max_adc = 4000

    # vref: Voltage reference for adjustments to the voltage reading as the battery is drained
    @property
    def vref(self):
        return self._vref

    @vref.setter
    def vref(self, val):
        self._vref = val

    # vcut: Voltage cutoff when the battery is completely drained
    @property
    def vcut(self):
        return self._vcut

    @vcut.setter
    def vcut(self, val):
        self._vcut = val

    # max: Maximum ADC Reading when the battery is fully charged
    @property
    def max_adc(self):
        return self._max_adc

    @max_adc.setter
    def max_adc(self, val):
        self._max_adc = val

    ######################
    # Main Methods

    def percent(self):
        prct = round(((self.voltage() - self._vcut) / (self._vmax - self._vcut)) * 100)
        if prct > 100:
            prct = 100
        elif prct < 0:
            prct = 0
        return prct

    def voltage(self):
        pin_val = sum([self._bat_pin.read() for i in range(50)]) / 50
        return ((pin_val / self._max_adc) * self._vref) * 1.24