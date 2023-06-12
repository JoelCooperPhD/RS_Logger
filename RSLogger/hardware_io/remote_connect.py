from digi.xbee.devices import XBeeNetwork, NetworkDiscoveryStatus, XBeeMessage, XBeeDevice
import re
import asyncio
import serial
from serial.tools.list_ports_windows import comports
from asyncio import get_running_loop
from time import time_ns, gmtime, time


class RemoteConnectionManager:
    """
    A class to manage the connection to a remote XBee device.
    """
    DONGLE_ID = {'pid': 0x6015, 'vid': 0x0403}
    BAUD = 921600

    def __init__(self, dongle: XBeeDevice = None, distribute_cb=None, debug=False):
        """
        Initialize the connection manager with a dongle, a distribution callback, and a debug flag.
        """
        self._debug = debug
        self._dongle = dongle
        self._distribute = distribute_cb if distribute_cb else lambda a, b, c, d: print(f'No distribute callback: {a}, {b}, {c}, {d}')
        self._network = None
        self._dongle = None

        self._devices = dict()

    async def run(self):
        """
        Run the connection manager by starting to scan USB ports.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager.run")
        await asyncio.gather(self._scan_usb_ports())

    async def _scan_usb_ports(self):
        """
        Periodically scan USB ports for the dongle.
        """
        while True:
            if self._debug: print(f"{time_ns()} RemoteConnectionManager._scan_usb_ports")
            dongle = self._scan_for_dongle(await self._get_comports())

            if not dongle and self._dongle:
                self._close_dongle_connection()

            if dongle == 'New':
                self._xb_initialize()

            await asyncio.sleep(.5)

    async def _get_comports(self):
        """
        Get a list of all connected COM ports.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager._get_comports")
        loop = get_running_loop()
        return await loop.run_in_executor(None, comports)

    def _scan_for_dongle(self, comports):
        """
        Scan the given COM ports for the dongle and open a connection if found.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager._scan_for_dongle")
        for comport in comports:
            if comport.pid == self.DONGLE_ID['pid'] and comport.vid == self.DONGLE_ID['vid']:
                if not self._dongle:
                    self._dongle = XBeeDevice(comport.name, self.BAUD)
                    return 'New'
                else:
                    return 'Existing'
        return None

    def _close_dongle_connection(self):
        """
        Close the connection to the dongle.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager._close_dongle_connection")
        if self._dongle is not None:
            try:
                self._dongle.close()
            except Exception as e:
                print("Error while closing dongle: ", str(e))
            finally:
                self._dongle = None

    def _xb_initialize(self):
        """
        Initialize XBee device and network if not already initialized.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager._xb_initialize")
        if not self._dongle.is_open():
            self._dongle.open()
            self._dongle.add_data_received_callback(self._msg_received)
            if self._debug: print(f"{time_ns()} RemoteConnectionManager.update {self._dongle.is_open()}")

            self.start_network_scan()

    def _msg_received(self, msg: XBeeMessage):
        """
        Handle received messages from the XBee device.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager._msg_received {msg.data}")
        if msg:
            id = msg.remote_device.get_node_id()
            if id:
                pattern = r"(\w+)\s*[_ ]?\s*(\d+)"
                match = re.match(pattern, id)
                device_type, dev_id = match.groups()[0], match.groups()[1]
                self._distribute(device_type, id, msg.data, msg.timestamp)

    def start_network_scan(self):
        """
        Start scanning for devices on the network. If the network is not set up yet,
        initialize it first.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager.start_network_scan")
        if not self._network:
            self._network: XBeeNetwork = self._dongle.get_network()
            self._network.add_discovery_process_finished_callback(self._add_devices)
        self._network.start_discovery_process()

    def stop_network_scan(self):
        """
        Stop scanning for devices on the network and clean up the network object.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager.stop_network_scan")
        self._network.del_discovery_process_finished_callback(self._discovery_complete_callback)
        self._network.stop_discovery_process()
        self._network = None

    def clear_network(self):
        """
        Clear the devices found on the network and restart the network scan.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager.clear_network")
        self.stop_network_scan()
        self.start_network_scan()
        self._network.clear()

    def _add_devices(self, e: NetworkDiscoveryStatus):
        """
        Callback function that is called when the network discovery process is finished.
        If the process was successful, this method processes the discovered devices.
        If no devices were found, the discovery process is restarted.
        """
        if self._debug: print(f"{time_ns()} RemoteConnectionManager._add_devices")
        if e.value[1] == "Success":
            devices = self._network.get_devices()
            if devices:
                self._discovery_complete_callback(self._network.get_devices())
            else:
                self.start_network_scan()

    def _discovery_complete_callback(self, remote_devices):
        """
        Callback function that is called when the network discovery process is finished.
        """
        for d in remote_devices:
            if self._debug: print(f"{time_ns()} RemoteConnectionManager._process_device")
            id = re.sub(r'[_\s]', '', d.get_node_id())
            dev_num = re.match(r"([a-z]+)([0-9]+)", id, re.I)
            if dev_num:
                dev, num = dev_num.groups()
                self._devices.setdefault(dev, {})[num] = d
                self._distribute(dev, 'ui', 'devices', {",".join(list(self._devices[dev].keys()))})

                self._set_rtc(dev)

    def _set_rtc(self, dev):
        """
        Set the real time clock (RTC).
        """
        if self._debug: print(f" RemoteConnectionManager._set_rtc")
        tt = gmtime()
        self._distribute(dev, 'all', 'set_rtc', f"{tt[0]},{tt[1]},{tt[2]},{tt[6]},{tt[3]},{tt[4]},{tt[5]},123")


if __name__ == "__main__":
    UPS = RemoteConnectionManager(debug=False)
    asyncio.run(UPS.run())