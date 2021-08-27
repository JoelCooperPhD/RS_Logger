from asyncio import create_task, Event
from devices.drt_sft import usb_connect
from devices.utilities import loop_monitor


class SFTController:
    def __init__(self, q2c):
        self.q2c = q2c
        self.conman = usb_connect.ConnectionManager()

    async def update(self):
        create_task(self.conman.update())
        create_task(self._connect_event())

    async def _connect_event(self):
        while 1:
            connection = await self.conman.new_connection()
            print(connection)
