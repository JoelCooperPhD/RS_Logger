import serial.serialutil

from devices.utilities.HardwareInterface import USBConnect, Results
import asyncio
from queue import SimpleQueue
from serial.serialutil import SerialException


class SFTController:
    def __init__(self, hardware_interface_q_sft, user_interface_q_sft):
        self._q2_sft_hi: SimpleQueue = hardware_interface_q_sft
        self._q2_sft_ui: SimpleQueue = user_interface_q_sft

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
        asyncio.create_task(self._handle_messages_for_sft_hardware_interface())

    async def _connect_event(self):
        while True:
            self._connected_sft_devices = await self._connection_manager.new_connection()
            self._connected_sft_ports = ','.join(list(self._connected_sft_devices.keys()))
            msg = f'devices>{self._connected_sft_ports}'
            self._q2_sft_ui.put(msg)

            if self._connected_sft_devices:
                self._listen_to_connected_sft = True
            else:
                self._listen_to_connected_sft = False

    async def _handle_messages_from_sft_devices(self):
        def read_bytes(device_connection):
            msg = device_connection.read_until(b'\r\n').strip()
            return msg

        while 1:
            if self._connected_sft_devices:
                for port in self._connected_sft_devices:
                    try:
                        if self._connected_sft_devices[port].inWaiting():
                            loop = asyncio.get_running_loop()
                            msg = await loop.run_in_executor(None, read_bytes, self._connected_sft_devices[port])
                            msg = str(msg, 'utf-8').strip()

                            self._q2_sft_ui.put(f'cfg>{msg}')
                    except SerialException:
                        pass

            await asyncio.sleep(.001)

    async def _handle_messages_for_sft_hardware_interface(self):
        while 1:
            if self._connected_sft_devices:
                while not self._q2_sft_hi.empty():
                    msg = self._q2_sft_hi.get()
                    msg = msg.split(">")
                    to_send = ','.join(msg[1:])
                    port = msg[0]

                    if msg[0] in ['init', 'close']:
                        pass
                    elif msg[0] in ['start', 'stop']:
                        for d in self._connected_sft_devices:
                            asyncio.create_task(self._message_device(self._connected_sft_devices[d], to_send))
                    else:
                        asyncio.create_task(self._message_device(self._connected_sft_devices[port], to_send))
            await asyncio.sleep(.001)


    @staticmethod
    async def _message_device(serial_conn, cmd, value=None):
        if value:
            msg = str.encode(f'{cmd},{value}\n')
        else:
            msg = str.encode(f'{cmd}\n')
        serial_conn.write(msg)

    def _exit_async_loop(self):
        self._run = False
