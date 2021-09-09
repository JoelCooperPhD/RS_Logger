from devices.utilities.Model import mUSBConnect, mResults
import asyncio
from queue import SimpleQueue


class SFTController:
    def __init__(self, hardware_interface_q_sft, user_interface_q_sft):
        self._q2_sft_hi: SimpleQueue = hardware_interface_q_sft
        self._q2_sft_ui: SimpleQueue = user_interface_q_sft

        self._connection_manager = mUSBConnect.ConnectionManager(name='DRT_SFT', vid='F055', pid='9800')
        self._results_writer = mResults.ResultsWriter('DRT_SFT')

        self._connected_sft_devices = None
        self._connected_sft_ports = None

        # uart port
        self.msg_time_stamp = None
        self.msg_port = None
        self._run = True

    def update(self):
        t = asyncio.create_task(self._connection_manager.update())
        t1 = asyncio.create_task(self._connect_event())

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
            return device_connection.read_until(b'\r\n').strip()

        while 1:
            while self._listen_to_connected_sft:
                for port in self._connected_sft_devices:
                    if self._connected_sft_devices[port].inWaiting():

                        msg = await asyncio.get_running_loop().\
                            run_in_executor(None, read_bytes(self._connected_sft_devices[port]))
                        msg = str(msg, 'utf-8').strip()

                        self._q2_sft_ui.put(msg)

                await asyncio.sleep(.001)
            await asyncio.sleep(1)

    async def _handle_messages_from_sft_user_interface(self):
        while 1:
            while self._listen_to_connected_sft:
                if self._connected_sft_devices:
                    while not self._q2_sft_hi.empty():
                        msg = self._q2_sft_hi.get()
                        port, cmd, arg = msg.split(">")

                        if cmd in ['data_record', 'data_pause']:
                            for d in self._connected_sft_devices:
                                asyncio.create_task(self._message_device(self._connected_sft_devices[d], f'{cmd},{arg}'))
                        else:
                            asyncio.create_task(self._message_device(self._connected_sft_devices[port], f'{cmd},{arg}'))
                await asyncio.sleep(.001)
            await asyncio.sleep(1)

    @staticmethod
    async def _message_device(serial_conn, cmd, value=None):
        if value:
            msg = str.encode(f'{cmd},{value}\n')
        else:
            msg = str.encode(f'{cmd}\n')
        serial_conn.write(msg)

    def _exit_async_loop(self):
        self._run = False
