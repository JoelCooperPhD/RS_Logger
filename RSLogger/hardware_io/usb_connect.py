import asyncio
import serial
from serial.tools.list_ports_windows import comports
from asyncio import get_running_loop
from serial.serialutil import SerialException
from time import time_ns, gmtime, time

BAUD = 921600


class UsbPortScanner:
    """
    Class to scan USB ports and listen for messages from devices.
    """
    DEVICE_IDS = {'sftDRT': {'pid': 0xF055,  'vid': 0x9800},
                  'sDRT'  : {'pid': 0x801E,  'vid': 0x239A},
                  'wDRT'  : {'pid': 0x457 , 'vid': 0xF056},
                  'sVOG'  : {'pid': 0x0483,  'vid': 0x16C0},
                  'wVOG'  : {'pid': 0x08AE,  'vid': 0xf057}}

    def __init__(self, devices: dict, distribute_cb=None, debug=False):
        self._rs_devices = devices
        if not distribute_cb:
            self._distribute_cb = lambda a, b, c, d: print(f'No distribute callback: {a}, {b}, {c}, {d}')
        else:
            self._distribute_cb = distribute_cb

        self._debug = debug
        self._new_ports = set()
        self._old_ports = set()
        self._all_com_devices = dict()

    async def run(self):
        await asyncio.gather(self.scan_usb_ports(),
                             self.usb_message_listener()
                             )

    async def usb_message_listener(self):
        await asyncio.sleep(1)
        if self._debug: print(f"{time_ns()} UsbPortScanner._usb_message_listener")
        while True:
            try:
                for rs_devices in self._rs_devices:
                    for each_com in self._rs_devices[rs_devices]:
                        if 'COM' in each_com:
                            if self._rs_devices[rs_devices][each_com].in_waiting:
                                msg = self._rs_devices[rs_devices][each_com].readline()
                                timestamp = time()
                                if self._debug: print(f"{time_ns()} UsbPortScanner._usb_message_listener {msg}")

                                self._distribute_cb(rs_devices, each_com, msg, timestamp)

            except (SerialException, KeyError, RuntimeError) as e:
                if self._debug: print(f'Exception usb_connect.UsbPortScanner.usb_message_listener: {e}')
            await asyncio.sleep(0.00001)

    async def scan_usb_ports(self):
        if self._debug: print(f"{time_ns()} UsbPortScanner.scan_usb_ports")
        while True:
            try:
                self._all_com_devices: serial.tools.list_ports_windows = await self._get_comports()
                self._new_ports = set([p for p in self._all_com_devices])

                to_add = self._new_ports.difference(self._old_ports)
                to_remove = self._old_ports.difference(self._new_ports)

                if to_add: asyncio.create_task(self._add_devices(to_add))
                if to_remove: self._remove_devices(to_remove)

                self._old_ports = self._new_ports

            except RuntimeError:
                pass
            await asyncio.sleep(.5)

    async def _get_comports(self):
        if self._debug: print(f"{time_ns()} UsbPortScanner._get_comports")
        loop = get_running_loop()
        return await loop.run_in_executor(None, comports)

    async def _add_devices(self, to_add):
        await asyncio.sleep(.5)
        if self._debug: print(f"{time_ns()} UsbPortScanner._add_devices")
        for d in to_add:  # Cycle through newly connected devices
            for rs_devices in self.DEVICE_IDS:  # Cycle through our device ID's and look for a match
                if self.DEVICE_IDS[rs_devices]['pid'] == d.pid and self.DEVICE_IDS[rs_devices]['vid'] == d.vid:  # If a new device is one of ours
                    if rs_devices not in self._rs_devices or d.name not in self._rs_devices[rs_devices]:
                        try:
                            if rs_devices not in self._rs_devices:  # First of its kind so add a new device type
                                self._rs_devices.update({rs_devices: {d.name: serial.Serial(d.name, BAUD)}})
                            else:  # device type exists, add a new item on a new com port
                                self._rs_devices[rs_devices].update({d.name: serial.Serial(d.name, BAUD)})
                            self._set_device_rtc(rs_devices, d.name)
                        except SerialException as e:
                            print(f'Serial Exception in usb_connect: {e}')
                        try:
                            self._distribute_cb(rs_devices, 'ui', 'devices', ','.join(list(self._rs_devices[rs_devices].keys())))
                        except KeyError:
                            print("PORT ALREADY IN USE")

    def _remove_devices(self, to_remove):
        if self._debug: print(f"{time_ns()} UsbPortScanner._remove_devices")
        ours_removed = dict()
        for d in to_remove:  # cycle through devices that need to be removed
            for rs_devices in self._rs_devices:  # Cycle through each device type (e.g., 'VOG', 'DRT', etc)
                for port in self._rs_devices[rs_devices]:  # Cycle through the ports for each device
                    if port == d.name: ours_removed.update({rs_devices: {port: d}})
        for rs_devices in ours_removed:
            for port in ours_removed[rs_devices]:
                del self._rs_devices[rs_devices][port]
                self._distribute_cb(rs_devices, 'ui', 'devices', ','.join(list(self._rs_devices[rs_devices].keys())))

    def _set_device_rtc(self, device, port):
        if self._debug: print(f"{time_ns()} UsbPortScanner._set_device_rtc")
        tt = gmtime()
        val = f'{tt[0]},{tt[1]},{tt[2]},{tt[6]},{tt[3]},{tt[4]},{tt[5]},123'
        self._distribute_cb(device, port, 'set_rtc', val)


if __name__ == "__main__":
    UPS = UsbPortScanner(devices=dict(), debug=True)
    asyncio.run(UPS.run())
