import asyncio
from devices.DRT_SFT.Model import mController as sft_controller
from devices.utilities import loop_monitor


class RootController:
    def __init__(self, q2v, q2c):
        self._q2v = q2v
        self._q2c = q2c
        self._route_messages = True
        self.loop_monitor = loop_monitor.LoopMonitor()
        # Devices
        self._devices = {'DRT_SFT': sft_controller.SFTController(q2c, q2v)}

    async def run(self):
        for d in self._devices:
            asyncio.create_task(self._devices[d].update())

        # asyncio.create_task(self.loop_monitor.run_asyncio())

        await asyncio.create_task(self._monitor_main2c())

    async def _monitor_main2c(self):
        while self._route_messages:
            while not self._q2c.empty():
                msg = self._q2c.get()
                kv = msg.split(">")

                if 'ctrl' in kv:
                    # Send to all device controllers
                    pass

                elif kv[0] == 'exit':
                    self._route_messages = False

                else:
                    print(f"controller_main: {msg} message not routed")

            await asyncio.sleep(.01)

