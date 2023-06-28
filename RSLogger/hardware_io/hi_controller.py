import asyncio
from time import time_ns
from RSLogger.hardware_io.usb_connect import UsbPortScanner
from RSLogger.hardware_io.remote_connect import RemoteConnectionManager
from RSLogger.hardware_io.sDRT_HI import sDRT_HIController
from RSLogger.hardware_io.wDRT_HI import wDRT_HIController
from RSLogger.hardware_io.wVOG_HI import wVOG_HIController
from RSLogger.hardware_io.sVOG_HI import sVOG_HIController
from queue import SimpleQueue
import inspect
import os


class HWRoot:
    def __init__(self, queues, debug=False):
        self._debug = debug
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}")

        self.q_2_ui: SimpleQueue = queues['q_2_ui']
        self.q_2_hi: SimpleQueue = queues['q_2_hi']

        self.RS_devices = dict()

        self._device_controllers = {
            'sDRT': sDRT_HIController.sDRTController(self.q_2_ui),
            'wDRT': wDRT_HIController.wDRTController(self.q_2_ui),
            'sVOG': sVOG_HIController.sVOGController(self.q_2_ui),
            'wVOG': wVOG_HIController.wVOGController(self.q_2_ui)
        }

        # Connection Managers
        self.XB = RemoteConnectionManager(self.RS_devices, self.distribute_message)
        self.USB = UsbPortScanner(self.RS_devices, self.distribute_message)

        self.launch()

    def launch(self):
        if not __name__ == "__main__":
            asyncio.run(self.run())

    async def run(self):
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}")

        await asyncio.gather(self.USB.run(),
                             self.XB.run(),
                             self._q_2_hi_messages_listener())

    async def _q_2_hi_messages_listener(self):
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}")

        while True:
            if not self.q_2_hi.empty():
                raw_packet = self.q_2_hi.get()
                try:
                    device, port, key, val = raw_packet.split('>')
                    self.distribute_message(device, port, key, val)
                    if key == 'net_scn':
                        self.XB.clear_network()
                except ValueError:
                    if self._debug:
                        print(f'{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}: {raw_packet}')
            await asyncio.sleep(0.001)

    def distribute_message(self, device, port, key, val):
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}: {device} {port} {key} {val}")

        if port == 'ui':
            self._handle_message_for_ui(device, port, key, val)
        else:
            self._handle_message_for_all_hardware_communication(device, port, key, val)

    def _handle_message_for_ui(self, device, port, key, val):
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}: {device} {port} {key} {val}")

        self.q_2_ui.put(f'{device}>{port}>{key}>{val}')

    def _handle_message_for_all_hardware_communication(self, device, port, key, val):
        if self._debug:
            print(f"{time_ns()} {self.file_()[:-3]}.{self.class_()}.{self.method_()}")

        if device == 'all':
            for dev, port_sockets in self.RS_devices.items():  # All devices
                for port in port_sockets.keys():  # All ports of device
                    socket = self.RS_devices.get(dev, {}).get(port)
                    self._device_controllers[dev].parse_command(socket, key, val, self.XB.xcvr)
        else:
            if port == 'all':
                for port in self.RS_devices[device]:
                    socket = self.RS_devices.get(device, {}).get(port)
                    self._device_controllers[device].parse_command(socket, key, val, self.XB.xcvr)
            else:
                if socket := self.RS_devices.get(device, {}).get(port):
                    self._device_controllers[device].parse_command(socket, key, val, self.XB.xcvr)

    def file_(self):
        return os.path.basename(__file__)

    def class_(self):
        return self.__class__.__name__

    def method_(self):
        return  inspect.currentframe().f_back.f_code.co_name


if __name__ == "__main__":
    queues = {'q_2_ui': SimpleQueue(), 'q_2_hi': SimpleQueue()}
    hw_root = HWRoot(queues, debug=True)
    asyncio.run(hw_root.run())

