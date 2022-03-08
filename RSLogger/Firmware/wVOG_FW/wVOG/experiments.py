import uasyncio as asyncio
from pyb import Pin
from wVOG import lenses
import time

class Peek:
    def __init__(self, config=None, results_cb=None):
        self._cfg = config
        self._results_cb = results_cb
     