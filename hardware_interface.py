import asyncio
from devices.DRT_SFT.HardwareInterface import SFT_HIController as sft_controller
from devices.utilities import loop_monitor


class HardwareInterface:
    def __init__(self, hardware_interface_qs, user_interface_qs):
        self._HI_queues = hardware_interface_qs
        self._UI_queues = user_interface_qs
        self._route_messages = True
        self.loop_monitor = loop_monitor.LoopMonitor()
        # Devices
        self._devices = {'SFT': sft_controller.SFTController(self._HI_queues['sft'], self._UI_queues['sft'])}

    async def run(self):
        for d in self._devices:
            self._devices[d].update()

        # asyncio.create_task(self.loop_monitor.run_asyncio())

        await asyncio.create_task(self._monitor_main2c())

    async def _monitor_main2c(self):
        while self._route_messages:
            while not self._HI_queues['root'].empty():
                msg = self._HI_queues['root'].get()

                if 'cmd' in msg:
                    for d in self._HI_queues:
                        if d != 'root':
                            self._HI_queues[d].put(msg)
                    pass

                elif 'exit' in msg:
                    self._route_messages = False

                else:
                    print(f"HI Root: {msg} message not routed")

            await asyncio.sleep(.01)

