from threading import Thread
from RSLogger.HardwareInterface._utilities import USBConnect
from asyncio import create_task, sleep
from queue import SimpleQueue
from serial.serialutil import SerialException
from time import time


class SFTController:
    def __init__(self, q_main, q_hi_sft):
        self._q_out: SimpleQueue = q_main
        self._q_in: SimpleQueue = q_hi_sft

        self._connection_manager = USBConnect.ConnectionManager(name='sft', vid='F055', pid='9800')

        self._connected_sft_devices = None
        self._connected_sft_ports = None

        # uart port
        self.msg_time_stamp = None
        self.msg_port = None
        self._run = True

        self._file_path = None
        self._cond_name = ""

    def run(self):
        create_task(self._connection_manager.update())
        create_task(self._connect_event())
        create_task(self._handle_messages_from_sft_devices())
        create_task(self._queue_monitor())

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
                            timestamp = time()
                            msg = str(msg, 'utf-8').strip()
                            key, val = msg.split('>')
                            if key == 'dta':
                                dta_split = val.split(',')
                                sub_str = ', '.join(dta_split[2:])
                                self._log_results(f'sft_{port}, {self._cond_name}, {timestamp}, {sub_str}')
                                self._q_out.put(f'ui_sft>trl>{port},{dta_split[4]}')
                                if dta_split[5] == '-1':
                                    self._q_out.put(f'ui_sft>rt>{port},-1')

                            elif key in ['VIB', 'LED', 'AUD']:
                                self._q_out.put(f'ui_sft>stm>{port},{val}')
                            elif key in ['clk', 'trl', 'rt']:
                                self._q_out.put(f'ui_sft>{key}>{port},{val}')
                            else:
                                self._q_out.put(f'ui_sft>{msg}')
                    except SerialException:
                        pass

            await sleep(0.0001)

    async def _queue_monitor(self):
        while 1:
            if self._connected_sft_devices:
                while not self._q_in.empty():
                    msg = self._q_in.get()
                    address, key, val = msg.split(">")

                    if val == 'ALL':
                        if 'cond' in key:
                            self._cond_name = key.split(':')[1]
                        else:
                            for val in self._connected_sft_devices:
                                create_task(self._message_device(self._connected_sft_devices[val], key))
                    elif key == 'fpath':
                        self._file_path = val
                    else:
                        create_task(self._message_device(self._connected_sft_devices[val], key))
            await sleep(0.0001)

    def _log_results(self, data_packet):
        def _write(_path, _results):
            try:
                with open(_path, 'a') as writer:
                    writer.write(_results + '\n')
            except (PermissionError, FileNotFoundError):
                print("Control write error")
        file_path = f"{self._file_path}/sft.txt"
        t = Thread(target=_write, args=(file_path, data_packet))
        t.start()

    @staticmethod
    async def _message_device(serial_conn, cmd):
        serial_conn.write(str.encode(f'{cmd}\n'))

    def _exit_async_loop(self):
        self._run = False
