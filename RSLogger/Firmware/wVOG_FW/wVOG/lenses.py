import uasyncio as asyncio
import utime as time
import random
import pyb


class Lenses:
    def __init__(self):
        self._run_AC = True

        self._toggle_1 = pyb.Pin(pyb.Pin.board.Y3, pyb.Pin.OUT)
        self._toggle_2 = pyb.Pin(pyb.Pin.board.Y4, pyb.Pin.OUT)

        self._lens_a = pyb.Pin(pyb.Pin.board.X9, pyb.Pin.OUT)
        self._lens_b = pyb.Pin(pyb.Pin.board.X10, pyb.Pin.OUT)
        
        asyncio.create_task(self._arm_xformer())

    async def _arm_xformer(self):
        val = True
        while True:
            if self._run_AC:
                self._toggle_1.value(val)
                self._toggle_2.value(not val)
                val = not val
            else:
                self._toggle_1.value(0)
                self._toggle_2.value(0)
            await asyncio.sleep_ms(5)

    def clear(self, lenses=['a', 'b']):
        self._run_AC = True
        self._lens_a.value(1 if 'a' in lenses else 0)
        self._lens_b.value(1 if 'b' in lenses else 0)
        

    def opaque(self, lenses=['a', 'b']):
        self._run_AC = False
        self._toggle_1.value(0)
        self._toggle_2.value(0)
        self._lens_a.value(0 if 'a' in lenses else 1)
        self._lens_b.value(0 if 'b' in lenses else 1)


