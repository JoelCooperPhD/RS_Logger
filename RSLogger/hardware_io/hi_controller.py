import asyncio
from time import time_ns
from RSLogger.hardware_io.usb_connect import UsbPortScanner
from RSLogger.hardware_io.remote_connect import RemoteConnectionManager
from RSLogger.hardware_io.sDRT_HI import sDRT_HIController
from RSLogger.hardware_io.wDRT_HI import wDRT_HIController
from RSLogger.hardware_io.wVOG_HI import wVOG_HIController
from RSLogger.hardware_io.sVOG_HI import sVOG_HIController

from digi.xbee.devices import XBeeDevice
from queue import SimpleQueue


class HWRoot:
    def __init__(self, queues, debug=False):
        self._debug = debug
        if self._debug: print(f"{time_ns()} HWRoot.__init___")
        self.q_2_ui: SimpleQueue = queues['q_2_ui']
        self.q_2_hi: SimpleQueue = queues['q_2_hi']

        self.dongle: XBeeDevice = None
        self.devices = dict()

        self._device_controllers = {
            'sDRT': sDRT_HIController.sDRTController(self.q_2_ui),
            'wDRT': wDRT_HIController.wDRTController(self.q_2_ui),
            'sVOG': sVOG_HIController.sVOGController(self.q_2_ui),
            'wVOG': wVOG_HIController.wVOGController(self.q_2_ui)
        }

        # Connection Managers
        self.XB = RemoteConnectionManager(self.dongle, self.distribute_message)
        self.USB = UsbPortScanner(self.devices, self.distribute_message)

        self.launch()

    def launch(self):
        if not __name__ == "__main__":
            asyncio.run(self.run())

    async def run(self):
        if self._debug: print(f"{time_ns()} HWRoot.async_portal")
        await asyncio.gather(self.USB.run(),
                             self.XB.run(),
                             self._q_2_hi_messages_listener())

    async def _q_2_hi_messages_listener(self):
        if self._debug: print(f"{time_ns()} HWRoot._q_2_hi_message_listener")
        while True:
            if not self.q_2_hi.empty():
                raw_packet = self.q_2_hi.get()
                try:
                    device, port, key, val = raw_packet.split('>')
                    if self._debug: print(f"{time_ns()} HWRoot._q_2_hi_message_listener")
                    self.distribute_message(device, port, key, val)
                    if key == 'net_scn':
                        self.XB.clear_network()
                except ValueError:
                    print(f'hi_controller failed to parse: {raw_packet}')
            await asyncio.sleep(0.001)

    def distribute_message(self, device, port, key, val):
        if self._debug: print(f"{time_ns()} HWRoot.distribute_messages: {device} {port} {key} {val}")

        if port == 'ui':
            self._handle_message_for_ui(device, port, key, val)
        else:
            self._handle_message_for_all_hardware_communication(device, port, key, val)

    def _handle_message_for_ui(self, device, port, key, val):
        self.q_2_ui.put(f'{device}>{port}>{key}>{val}')

    def _handle_message_for_all_hardware_communication(self, device, port, key, val):
        if self._debug: print(f"{time_ns()} HWRoot._handle_message_for_all_hardware_communication")
        if device == 'all':
            for devices in [self.devices]:
                for dev, ports in self.devices.items():
                    for port in ports.keys():
                        self._route_msg_to_device_controllers(dev, port, key, val,
                                                              'com' if devices is self.devices else 'xb')
        else:
            if port == 'all':
                for devices in [self.devices]:
                    if device in devices.keys():
                        for port in self.devices[device].keys():
                            self._route_msg_to_device_controllers(device, port, key, val,
                                                                  'com' if devices is self.devices else 'xb')
            else:
                for devices in [self.devices]:
                    if device in self.devices.keys():
                        self._route_msg_to_device_controllers(device, port, key, val,
                                                              'com' if devices is self.devices else 'xb')

    def _route_msg_to_device_controllers(self, device, port, key, val, device_type):
        if self._debug: print(f"{time_ns()} HWRoot._route_msg_to_device_controllers:"
                              f"{device} {port} {key} {val} {device_type}")
        if socket := self.devices.get(device, {}).get(port):
            if device_type == 'com' and device != 'dongle':
                self._device_controllers[device].parse_command(socket, key, val)
            elif device_type == 'xb' and self.devices.get('dongle'):
                self._device_controllers[device].parse_command(socket, key, val,
                                                               next(iter(self.devices['dongle'].values())))


if __name__ == "__main__":
    queues = {'q_2_ui': SimpleQueue(), 'q_2_hi': SimpleQueue()}
    hw_root = HWRoot(queues, debug=True)
    asyncio.run(hw_root.run())

