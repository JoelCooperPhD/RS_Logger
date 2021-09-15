import asyncio
from devices.DRT_SFT.HardwareInterface import SFT_HIController as sft_controller
from devices.utilities import loop_monitor


class HardwareInterface:
    def __init__(self, queues):
        self._queues = queues
        self._q_in = queues['hi_root']
        self._q_out = queues['main']

        self._route_messages = True
        self._loop_monitor = loop_monitor.LoopMonitor()
        # Devices
        self._devices = {'SFT': sft_controller.SFTController(self._q_out, self._queues['hi_sft'])}

    async def run(self):
        for d in self._devices:
            self._devices[d].update()

        await asyncio.create_task(self._queue_monitor())

    async def _queue_monitor(self):
        while self._route_messages:
            while not self._q_in.empty():
                msg = self._q_in.get()
                address, key, val = msg.split('>')
                if key == 'exit':
                    self._route_messages = False

            await asyncio.sleep(.01)

