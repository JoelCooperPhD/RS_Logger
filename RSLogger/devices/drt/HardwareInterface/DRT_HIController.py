from serial import SerialException
from RSLogger.devices.common_utilities.HardwareInterface import USBConnect, Results
from threading import Thread
from queue import SimpleQueue
import asyncio
from time import time


class DRTController:
    def __init__(self, q_main, q_hi_drt):
        self._q_out: SimpleQueue = q_main
        self._q_in: SimpleQueue = q_hi_drt

        self._connection_manager = USBConnect.ConnectionManager(name='drt', vid='239', pid='801')
        self._results_writer = Results.ResultsWriter('drt')

        self._connected_drt_devices = None
        self._connected_drt_ports = None

        # uart port
        self.msg_time_stamp = None
        self.msg_port = None
        self._run = True

        self._file_path = None

        # results
        self._clicks = dict()
        self._results = dict()
        self._cond_name = ""

    def run(self):
        asyncio.create_task(self._handle_messages_from_drt_devices())
        asyncio.create_task(self._connection_manager.update())
        asyncio.create_task(self._connect_event())

        asyncio.create_task(self._queue_monitor())
        
    async def _connect_event(self):
        while 1:
            self._connected_drt_devices = await self._connection_manager.new_connection()
            self._connected_drt_ports = ','.join(list(self._connected_drt_devices.keys()))
            msg = f'ui_drt>devices>{self._connected_drt_ports}'
            self._q_out.put(msg)

            if self._connected_drt_devices:
                self._listen_to_connected_drt = True
            else:
                self._listen_to_connected_drt = False
        
    async def _handle_messages_from_drt_devices(self):
        while 1:
            if self._connected_drt_devices:
                for port in self._connected_drt_devices:
                    try:
                        if self._connected_drt_devices[port].inWaiting():
                            msg = self._connected_drt_devices[port].read_until(b'\r\n').strip()
                            timestamp = time()
                            msg = str(msg, 'utf-8').strip()

                            key, val = msg.split('>')

                            if key in ['clk', 'trl', 'stm', 'end']:
                                self._q_out.put(f'ui_drt>{key}>{port},{val}')
                                if key == 'clk':
                                    self._clicks[port] = val
                                elif key == 'trl':
                                    self._results[port] = val
                                elif key == 'end':
                                    self._log_results(port, timestamp)
                                elif msg == 'stm>1':
                                    self._clicks[port] = 0
                            else:
                                self._q_out.put(f'ui_drt>{msg}')
                    except SerialException:
                        pass
            await asyncio.sleep(.01)

    async def _queue_monitor(self):
        while 1:
            if self._connected_drt_devices:
                while not self._q_in.empty():
                    msg = self._q_in.get()
                    address, key, val = msg.split(">")

                    if val == 'ALL':
                        if 'cond' in key:
                            self._cond_name = key.split(':')[1]
                        else:
                            for val in self._connected_drt_devices:
                                asyncio.create_task(self._message_device(self._connected_drt_devices[val], key))
                    elif key == 'fpath':
                        self._file_path = val
                    else:
                        asyncio.create_task(self._message_device(self._connected_drt_devices[val], key))
            await asyncio.sleep(.01)

    def _log_results(self, port, timestamp):
        if len(self._clicks):
            d = self._results[port].split(',')

            # Old data format
            if len(d) == 3:
                data = f'{d[0]}, {d[1]}, {self._clicks[port]}, {d[2]}'

            # New data format
            else:
                data = f'{d[0]}, {d[1]}, {self._clicks[port]}, {d[3]}'

            packet = f'drt_{port}, {self._cond_name}, {timestamp}, {data}'

            def _write(_path, _results):
                try:
                    with open(_path, 'a') as writer:
                        writer.write(_results + '\n')
                except (PermissionError, FileNotFoundError):
                    pass

            file_path = f"{self._file_path}/drt.txt"
            t = Thread(target=_write, args=(file_path, packet))
            t.start()


    @staticmethod
    async def _message_device(serial_conn, cmd):
        if cmd in ['start', 'stop']:
            serial_conn.write(str.encode(f'exp_{cmd}\n'))
        elif any([c in cmd for c in ['get', 'set', 'stim']]):
            serial_conn.write(str.encode(f'{cmd}\n'))
        elif cmd == 'iso':
            for msg in ['set_lowerISI 3000', 'set_upperISI 5000', 'set_stimDur 1000', 'set_intensity 255']:
                serial_conn.write(str.encode(f'{msg}\n'))
                await asyncio.sleep(0)

        await asyncio.sleep(0)

    @staticmethod
    async def _send_msg_to_devices(serial_conn, msg):
        serial_conn.write(str.encode(f'{msg}\n'))

    def _exit_async_loop(self):
        self._run = False
