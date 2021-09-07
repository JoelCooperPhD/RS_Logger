from asyncio import create_task
from devices.utilities.Model import mUSBConnect, mResults
from devices.DRT_SFT.HardwareInterface import SFT_HIDeviceInterface
import asyncio
from queue import SimpleQueue


class SFTController:
    def __init__(self, q2c: SimpleQueue, q2v: SimpleQueue):
        self.q2c = q2c
        self.q2v = q2v

        self._connection_manager = mUSBConnect.ConnectionManager(name='DRT_SFT', vid='F055', pid='9800')
        self._hwi = SFT_HIDeviceInterface.SFTModel()
        self._results_writer = mResults.ResultsWriter('DRT_SFT')

        self._connected_sft_devices = None

        # uart port
        self.msg_time_stamp = None
        self.msg_port = None
        self._run = True

        # DRT HardwareInterface
        self._drt_m = SFT_HIDeviceInterface.SFTModel()

    async def update(self):
        create_task(self._connection_manager.update())
        create_task(self._connect_event())

    async def _connect_event(self):
        while 1:
            self._connected_sft_devices = await self._connection_manager.new_connection()
            if self._connected_sft_devices:
                self._listen_to_connected_sft = True

    async def _handle_messages_from_sft_devices(self):
        def read_bytes(device_connection):
            return device_connection.read_until(b'\r\n').strip()

        while 1:
            for port in self._connected_sft_devices:
                if self._connected_sft_devices[port].inWaiting():

                    msg = await asyncio.get_running_loop().run_in_executor(None, read_bytes(self._connected_sft_devices[port]))
                    msg = str(msg, 'utf-8').strip()

                    cmd, arg = msg.split(">")

                    self.q2v.put(msg)

            await asyncio.sleep(.001)

    async def _handle_messages_from_sft_ui(self):
        while 1:
            if self._connected_sft_devices:
                while not self.q2c.empty():
                    msg = self.q2c.get()
                    port, cmd, arg = msg.split(">")

                    if cmd in ['data_record', 'data_pause']:
                        for d in self._connected_sft_devices:
                            asyncio.create_task(self._hwi.send(self._connected_sft_devices[d], f'{cmd},{arg}'))
                    else:
                        asyncio.create_task(self._hwi.send(self._connected_sft_devices[port], f'{cmd},{arg}'))
            await asyncio.sleep(.001)

    def _exit_async_loop(self):
        self._run = False
