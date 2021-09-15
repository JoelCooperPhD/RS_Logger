import serial.serialutil

from devices.utilities.HardwareInterface import USBConnect, Results
import asyncio
from queue import SimpleQueue
from serial.serialutil import SerialException


class SFTController:
    def __init__(self, q_main, q_hi_sft):
        self._q_out: SimpleQueue = q_main
        self._q_in: SimpleQueue = q_hi_sft

        self._connection_manager = USBConnect.ConnectionManager(name='DRT_SFT', vid='F055', pid='9800')
        self._results_writer = Results.ResultsWriter('DRT_SFT')

        self._connected_sft_devices = None
        self._connected_sft_ports = None

        # uart port
        self.msg_time_stamp = None
        self.msg_port = None
        self._run = True

    def update(self):

        asyncio.create_task(self._connection_manager.update())
        asyncio.create_task(self._connect_event())
        asyncio.create_task(self._handle_messages_from_sft_devices())
        asyncio.create_task(self._queue_monitor())

    async def _connect_event(self):
        while True:
            self._connected_sft_devices = await self._connection_manager.new_connection()
            self._connected_sft_ports = ','.join(list(self._connected_sft_devices.keys()))
            msg = f'ui_sft>devices>{self._connected_sft_ports}'
            self._q_out.put(msg)

            if self._connected_sft_devices:
                self._listen_to_connected_sft = True
            else:
                self._listen_to_connected_sft = False

    async def _handle_messages_from_sft_devices(self):
        while 1:
            if self._connected_sft_devices:
                for port in self._connected_sft_devices:
                    try:
                        if self._connected_sft_devices[port].inWaiting():
                            msg = self._connected_sft_devices[port].read_until(b'\r\n').strip()
                            msg = str(msg, 'utf-8').strip()
                            self._q_out.put(f'ui_sft>{msg}')
                    except SerialException:
                        pass

            await asyncio.sleep(.01)

    async def _queue_monitor(self):
        while 1:
            if self._connected_sft_devices:
                while not self._q_in.empty():
                    msg = self._q_in.get()
                    address, key, val = msg.split(">")

                    if val == 'ALL':
                        for val in self._connected_sft_devices:
                            asyncio.create_task(self._message_device(self._connected_sft_devices[val], key))
                    else:
                        asyncio.create_task(self._message_device(self._connected_sft_devices[val], key))
            await asyncio.sleep(.01)

    @staticmethod
    async def _message_device(serial_conn, cmd):
        serial_conn.write(str.encode(f'{cmd}\n'))
        print(f'{cmd}\n')

    def _exit_async_loop(self):
        self._run = False
