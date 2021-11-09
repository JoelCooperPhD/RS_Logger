import pyb
import select
import uasyncio as asyncio
from time import time, ticks_ms, ticks_diff

class Diagnostics:
    def __init__(self):
        pass
    
    async def heartbeat(self):
        while True:
            tic = ticks_ms()
            await asyncio.sleep(1)
            print(ticks_diff(ticks_ms(), tic))
