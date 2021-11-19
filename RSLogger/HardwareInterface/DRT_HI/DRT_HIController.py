from serial import SerialException
from RSLogger.HardwareInterface._utilities import USBConnect
from threading import Thread
from queue import SimpleQueue
from asyncio import create_task, sleep
from time import time


class DRTController:
    def __init__(self, q_main, q_hi_drt):
        self._q_out: SimpleQueue = q_main
        self._q_in: SimpleQueue = q_hi_drt

        self._connection_manager = USBConnect.ConnectionManager(name='drt', vid='239', pid='801')

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
        create_task(self._handle_messages_from_drt_devices())
        create_task(self._connection_manager.update())
        create_task(self._connect_event())

        create_task(self._queue_monitor())
        
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
                    except (SerialException, ValueError):
                        pass
            await sleep(0.0001)

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
                                create_task(self._message_device(self._connected_drt_devices[val], key))
                    elif key == 'fpath':
                        self._file_path = val
                    else:
                        create_task(self._message_device(self._connected_drt_devices[val], key))
            await sleep(0.0001)

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
        try:
            if cmd in ['start', 'stop']:
                serial_conn.write(str.encode(f'exp_{cmd}\n'))
            elif any([c in cmd for c in ['get', 'set', 'stim']]):
                serial_conn.write(str.encode(f'{cmd}\n'))
            elif cmd == 'iso':
                for msg in ['set_lowerISI 3000', 'set_upperISI 5000', 'set_stimDur 1000', 'set_intensity 255']:
                    serial_conn.write(str.encode(f'{msg}\n'))
                    await sleep(0.0001)
        except Exception as e:
            print(f"DRT message_device exception: {e}")

        await sleep(0.0001)

    def _exit_async_loop(self):
        self._run = False
