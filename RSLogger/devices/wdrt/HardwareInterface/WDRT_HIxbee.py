from serial.tools.list_ports import comports
import asyncio
from digi.xbee.devices import XBeeDevice, XBeeNetwork, NetworkDiscoveryStatus

class ConnectionManager:
    def __init__(self):
        self._baud = 921600

        self._ports_old = list()

        self._known_xcvrs = set()
        self._xcvr = None

        self._network = None
        self.devices = set()
        self._devices_pid = '6015'

        # These queues pass the xcvr and remote units respectively
        self.attached_xcvr_q = asyncio.Queue()
        self.networked_devices_q = asyncio.Queue()

        # All messages from xb units are passed via this queue
        self.xb_msg_q = asyncio.Queue()

        asyncio.create_task(self._scan_for_xcvr())

    ####################################################
    # Xbee Dongle
    async def _scan_for_xcvr(self):
        ports_old = list()
        self._xcvr = None
        loop = asyncio.get_running_loop()
        while True:
            ports = await loop.run_in_executor(None, comports)
            ports = [p.name for p in ports if self._devices_pid in p.hwid]

            to_add = list(set(ports) - set(ports_old))
            if to_add and not self._xcvr:
                self._xcvr = XBeeDevice(to_add[0], self._baud)
                self._xcvr.open()
                self.attached_xcvr_q.put_nowait(self._xcvr)
                self._xcvr.add_data_received_callback(self._msg_received)

            to_remove = list(set(ports_old) - set(ports))
            if self._xcvr:
                if self._xcvr.serial_port in to_remove:
                    self._xcvr = None
                    self.attached_xcvr_q.put_nowait(self._xcvr)

            ports_old = ports

            await asyncio.sleep(1)

    def _msg_received(self, msg):
        self.xb_msg_q.put_nowait(msg)

    ####################################################
    # Remote Xbee devices
    def start_network_scan(self):
        if not self._network:
            self._network: XBeeNetwork = self._xcvr.get_network()
            self._network.add_discovery_process_finished_callback(self._add_devices)
        self._network.start_discovery_process()

    def stop_network_scan(self):
        self._network: XBeeNetwork
        self._network.del_discovery_process_finished_callback(self._add_devices)
        self._network.stop_discovery_process()
        self._network = None

    def clear_network(self):
        self.stop_network_scan()
        self.start_network_scan()
        self.devices.clear()
        self._network.clear()

    def _add_devices(self, e: NetworkDiscoveryStatus):
        if e.value[1] == "Success":
            new = set(self._network.get_devices())
            to_add = new - self.devices
            if to_add:
                self.devices.update(to_add)
                self.networked_devices_q.put_nowait(self.devices)
            else:
                self.start_network_scan()

        else:
            self.start_network_scan()
