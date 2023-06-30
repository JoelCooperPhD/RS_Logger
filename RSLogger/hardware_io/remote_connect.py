from digi.xbee.devices import XBeeNetwork, NetworkDiscoveryStatus, XBeeMessage, XBeeDevice
import re
import asyncio
from serial.tools.list_ports_windows import comports
from asyncio import get_running_loop
from time import time_ns, gmtime


class RemoteConnectionManager:
    DEVICE_IDS = {'sftDRT': {'pid': 0xF055,  'vid': 0x9800},
                  'sDRT'  : {'pid': 0x801E,  'vid': 0x239A},
                  'wDRT'  : {'pid': 0x457 , 'vid': 0xF056},
                  'sVOG'  : {'pid': 0x0483,  'vid': 0x16C0},
                  'wVOG'  : {'pid': 0x08AE,  'vid': 0xf057}}
    DONGLE_ID = {'pid': 0x6015, 'vid': 0x0403}
    BAUD = 921600

    def __init__(self, remote_devices, distribute_cb=None, debug=False):
        self._debug = debug

        self.xcvr = None

        self._distribute = distribute_cb if distribute_cb else lambda a, b, c, d: print(f'No distribute callback: {a}, {b}, {c}, {d}')
        self._network = None

        self._remote_devices = remote_devices

    async def run(self):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager.run")
        await asyncio.gather(self._scan_usb_ports())

    async def _scan_usb_ports(self):
        while True:
            if self._debug:
                print(f"{time_ns()} RemoteConnectionManager._scan_usb_ports")
            dongle = self._scan_for_dongle(await self._get_comports())

            if not dongle and self.xcvr:
                self._close_dongle_connection()

            if dongle == 'New':
                self._xb_initialize()

            await asyncio.sleep(.5)

    async def _get_comports(self):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager._get_comports")
        loop = get_running_loop()
        return await loop.run_in_executor(None, comports)

    def _scan_for_dongle(self, comports):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager._scan_for_dongle")

        # Scan to make sure that no other RS devices are attached, if so then the dongle won't be connected.
        for comport in comports:
            for device in self.DEVICE_IDS:
                if comport.pid == self.DEVICE_IDS[device]['pid'] and comport.vid == self.DEVICE_IDS[device]['vid']:
                    self.xcvr = None
                    return 'Wired'

        for comport in comports:
            if comport.pid == self.DONGLE_ID['pid'] and comport.vid == self.DONGLE_ID['vid']:
                if not self.xcvr:
                    self.xcvr = XBeeDevice(comport.name, self.BAUD)
                    if self._debug: print(f"{time_ns()} RemoteConnectionManager._scan_for_dongle FOUND DONGLE")
                    return 'New'
                else:
                    return 'Existing'
        return None

    def _close_dongle_connection(self):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager._close_dongle_connection")
        if self.xcvr is not None:
            try:
                self.xcvr.close()
            except Exception as e:
                print("Error while closing dongle: ", str(e))
            finally:
                self.xcvr = None

    def _xb_initialize(self):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager._xb_initialize")
        if not self.xcvr.is_open():
            self.xcvr.open()
            self.xcvr.add_data_received_callback(self._msg_received)
            if self._debug: print(f"{time_ns()} RemoteConnectionManager.update {self.xcvr.is_open()}")

            self.start_network_scan()

    def _msg_received(self, msg: XBeeMessage):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager._msg_received {msg.data}")

        if self.xcvr:
            try:
                id_raw = msg.remote_device.get_node_id()
                id_clean = re.sub(r'[_\s]', '', id_raw)
                dev, num = re.match(r"([a-z]+)([0-9]+)", id_clean, re.I).groups()

                self._distribute(dev, id_raw, msg.data, msg.timestamp)
            except TypeError as e:
                if self._debug: print(f"{time_ns()} RemoteConnectionManager._msg_received ERROR {e}")

    def start_network_scan(self):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager.start_network_scan")

        if not self._network and self.xcvr:
            self._network: XBeeNetwork = self.xcvr.get_network()
            self._network.add_discovery_process_finished_callback(self._add_devices)
        if self._network:
            self._network.start_discovery_process()

    def stop_network_scan(self):
        if self._debug: print(f"{time_ns()} RemoteConnectionManager.stop_network_scan")
        self._network.del_discovery_process_finished_callback(self._discovery_complete_callback)
        self._network.stop_discovery_process()
        self._network = None

    def clear_network(self):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager.clear_network")
        self.stop_network_scan()
        self.start_network_scan()
        if self._network:
            self._network.clear()

    def _add_devices(self, e: NetworkDiscoveryStatus):
        if self._debug:
            print(f"{time_ns()} RemoteConnectionManager._add_devices")
        if e.value[1] == "Success":
            devices = self._network.get_devices()
            if devices:
                self._discovery_complete_callback(self._network.get_devices())
            else:
                self.start_network_scan()

    def _discovery_complete_callback(self, discovered_devices):
        for device in discovered_devices:
            if self._debug:
                print(f"{time_ns()} RemoteConnectionManager._discovery_complete_callback")

            try:
                id_raw = device.get_node_id()
                id_clean = re.sub(r'[_\s]', '', id_raw)

                dev_num = re.match(r"([a-z]+)([0-9]+)", id_clean, re.I)
                dev, num = dev_num.groups()

                self._remote_devices.setdefault(dev, {})[id_raw] = device

                device_d = ",".join(self._remote_devices[dev].keys())
                self._distribute(dev, 'ui', 'devices', device_d)
                self._set_rtc(dev, id_raw)
            except TypeError as e:
                if self._debug: print(f"{time_ns()} RemoteConnectionManager._discover_complete_callback ERROR {e}")

    def _set_rtc(self, dev, id_raw):
        if self._debug: print(f" RemoteConnectionManager._set_rtc {dev} {num}")
        tt = gmtime()
        self._distribute(dev, id_raw, 'set_rtc', f"{tt[0]},{tt[1]},{tt[2]},{tt[6]},{tt[3]},{tt[4]},{tt[5]},123")


if __name__ == "__main__":
    UPS = RemoteConnectionManager(dict(), debug=True)
    asyncio.run(UPS.run())
