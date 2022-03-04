import uasyncio as asyncio
import utime as time
import random

from wVOG import lenses

class wVOG:
    def __init__(self):
        self.lenses = lenses.LensControl()

    async def run(self):
        await asyncio.gather(
            self.lenses.run(),
            self.cycle_lenses(),
            self.heartbeat(),
        )

    async def heartbeat(self):
        while True:
            ticks_old = time.ticks_us()
            await asyncio.sleep(1)
            print(1000000 - time.ticks_diff(time.ticks_us(), ticks_old))

    async def cycle_lenses(self):
        while True:
            self.lenses.open_a()
            await asyncio.sleep(1)
            await asyncio.create_task(self.lenses.close(10))
            self.lenses.open_b()
            await asyncio.sleep(1)
            await asyncio.create_task(self.lenses.close(10))


# vog = wVOG()
# asyncio.run(vog.run())
