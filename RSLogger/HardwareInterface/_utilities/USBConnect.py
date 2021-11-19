import asyncio

from serial.tools.list_ports import comports
from asyncio import Event, sleep, get_running_loop
import serial
from serial import SerialException


class ConnectionManager:
    def __init__(self, name, vid, pid):
        self._name = name
        self._vid = vid
        self._pid = pid
        self._old_ports = list()
        self._known_rs_devices = dict()

        self._baud = 1152000

        self.paired_devices = dict()
        self.port_event = Event()

    async def update(self):
        while 1:
            try:
                loop = get_running_loop()
                new_ports = await loop.run_in_executor(None, comports)
                len_diff = len(new_ports) - len(self._old_ports)

                if len_diff != 0:
                    self._identify_rs_devices(new_ports)
                    await asyncio.sleep(.2)
                    if len_diff > 0:
                        self._connect_device()
                    else:
                        self._disconnect_device()

                    self.port_event.set()

                self._old_ports = new_ports
            except RuntimeError:
                pass
            await sleep(1)

    def _identify_rs_devices(self, ports):
        self._known_rs_devices.clear()
        for p in ports:
            if self._vid in p[2]:
                device_name = [self._name, self._vid, self._pid]
                self._known_rs_devices[p[0]] = device_name

    def _connect_device(self):
        to_add = {k: self._known_rs_devices[k] for k in set(self._known_rs_devices) - set(self.paired_devices)}
        try:
            for port in to_add:
                self.paired_devices[port] = serial.Serial(port, self._baud)
        except (FileNotFoundError, SerialException):
            pass

    def _disconnect_device(self):
        removed = {k: self.paired_devices[k] for k in set(self.paired_devices) - set(self._known_rs_devices)}
        for port in removed:
            try:
                self.paired_devices[port]['socket'].close()
            except TypeError:
                pass

            self.paired_devices.pop(port)

    async def new_connection(self):
        while 1:
            await self.port_event.wait()
            self.port_event.clear()

            return self.paired_devices
