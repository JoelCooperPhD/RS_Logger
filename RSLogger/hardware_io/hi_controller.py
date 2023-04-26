import asyncio
from serial.serialutil import SerialException
from serial import Serial
from time import gmtime
from digi.xbee.devices import RemoteRaw802Device

import re

from RSLogger.hardware_io.usb_connect import scan_usb_ports
from RSLogger.hardware_io.remote_connect import RemoteConnectionManager

from RSLogger.hardware_io.sDRT_HI import DRT_HIController
from RSLogger.hardware_io.wDRT_HI import WDRT_HIController
from RSLogger.hardware_io.wVOG_HI import WVOG_HIController
from RSLogger.hardware_io.sVOG_HI import SVOG_HIController


from time import time

class HWRoot:
    def __init__(self, queues):

        self._q_2_hi = queues['q_2_hi']
        self._q_2_ui = queues['q_2_ui']

        self._com_devices = {
            'dongle': dict(),
            'sftDRT': dict(),
            'sDRT'  : dict(),
            'wDRT'  : dict(),
            'sVOG'  : dict(),
            'wVOG'  : dict()
        }

        self._xb_devices = {
            'wDRT': dict(),
            'wVOG': dict()
        }

        self._device_controllers = {'sDRT': DRT_HIController.DRTController(self._q_2_ui),
                                    'wDRT': WDRT_HIController.WDRTController(self._q_2_ui),
                                    'sVOG': SVOG_HIController.SVOGController(self._q_2_ui),
                                    'wVOG': WVOG_HIController.WVOGController(self._q_2_ui)}

        self._remote_manifest_manager = RemoteConnectionManager(self._xb_network_scan_cb, self._xb_message_listener)

        self.async_portal()

    def async_portal(self):
        asyncio.run(self.run_main_async())

    async def run_main_async(self):
        await asyncio.gather(
            scan_usb_ports(self._usb_scan_cb),
            self._usb_message_listener(),
            self._q_2_hi_messages_listener(),
        )

    ######################################################################################
    # Queue 2 Hardware Interface (HI) Message Handler
    async def _q_2_hi_messages_listener(self):
        # Messages have the format "device,port>key>value"

        while 1:
            if not self._q_2_hi.empty():
                raw_packet = self._q_2_hi.get()
                try:
                    device_com, key, val = raw_packet.split('>')
                    device, port = device_com.split(',')
                    self._distribute_messages_to_controllers(device, port, key, val)

                    if key == 'net_scn':
                        self._remote_manifest_manager.clear_network()
                        for device in self._xb_devices:
                            self._xb_devices[device] = dict()

                except ValueError:
                    print(f'hi_controller failed to parse: {raw_packet}')

            await asyncio.sleep(.001)

    ######################################################################################
    # XB and USB Handlers
    def _xb_message_listener(self, device_type, device_id, msg, timestamp):
        self._message_handler(device_type, device_id, msg, timestamp)

    async def _usb_message_listener(self):
        while 1:
            for each_device in self._com_devices:
                for each_com in self._com_devices[each_device]:
                    if 'dongle' != each_device:
                        try:
                            if self._com_devices[each_device][each_com].in_waiting:
                                timestamp = time()
                                msg = self._com_devices[each_device][each_com].readline()
                                self._message_handler(each_device, each_com, msg, timestamp)

                        except SerialException:
                            pass

            await asyncio.sleep(.00001)

    def _message_handler(self, device, com, msg, timestamp):
        try:
            msg = str(msg, 'utf-8').strip()
            if msg:
                key, val = re.split(r"[|>]", msg)

                if key in ['dta', 'trl', 'data']:
                    if val[0] == ',': val = val[1:]
                    val = f'{timestamp},{val}'

                if msg:
                    self._q_2_ui.put(f'{device},{com}>{key}>{val}')
                self._distribute_messages_to_controllers(device, com, key, val)
        except ValueError as e:
            pass
            # print(f'HI Controller failed to parse: {e}')
    
    ######################################################################################
    # XB and USB Scan Callbacks
    def _xb_network_scan_cb(self, remote_devices):
        # Called from remote_connection when the network has completed scanning

        # Split up remote devices and populate xb_devices
        for d in remote_devices:
            d: RemoteRaw802Device
            pattern = r'(\w+)[\s_]*(\d+)'
            match = re.match(pattern, d.get_node_id())
            if match:
                dev, num = match.groups()
                if dev not in self._xb_devices:
                    self._xb_devices[dev] = {}
                self._xb_devices[dev][num] = d

        for dev in self._xb_devices:
            ports = list(self._xb_devices[dev].keys())
            if ports:
                msg = f'{dev},all>devices>{",".join(ports)}'
                self._q_2_ui.put(msg, ports)

        self._update_device_clocks()

    def _usb_scan_cb(self, connected_devices):
        # Iterate through usb_device dictionary, format, and put in q to ui
        self._com_devices = {device: dict() for device in self._com_devices}

        for each_com in connected_devices:
            device = connected_devices[each_com][0]
            socket = connected_devices[each_com][1]
            self._com_devices[device][each_com] = socket

        # If dongle then remove the wireless device com ports from the list
        for each_device in self._com_devices:
            if self._com_devices['dongle']:
                if 'w' in each_device:
                    self._com_devices[each_device] = dict()

        # Send all devices to ui
        for each_device in self._com_devices:
            if not self._com_devices['dongle']:
                self._q_2_ui.put(f'{each_device},all>devices>{",".join(list(self._com_devices[each_device].keys()))}')

        # Scan for wireless devices with the attached dongle
        if self._com_devices['dongle']:
            for com in self._com_devices['dongle']:
                self._remote_manifest_manager.update(self._com_devices['dongle'][com])
                break
        else:
            self._xb_devices = {dev: dict() for dev in self._xb_devices}

    def _update_device_clocks(self):
        tt = gmtime()
        time_gmt = f"{tt[0]},{tt[1]},{tt[2]},{tt[6]},{tt[3]},{tt[4]},{tt[5]},123"

        self._distribute_messages_to_controllers('all', 'all', 'set_rtc', time_gmt)

    ######################################################################################
    # Controller Distribution
    def _distribute_messages_to_controllers(self, device, port, key, val):
        if device == 'all':
            if port == 'all':
                # all, all - send to each devices and each port
                for each_dev in self._com_devices:
                    for each_port in self._com_devices[each_dev]:
                        self._route_com_msg_to_device_controllers(each_dev, each_port, key, val)
                for each_dev in self._xb_devices:
                    for each_port in self._xb_devices[each_dev]:
                        self._route_xb_msg_to_device_controllers(each_dev, each_port, key, val)
        else:
            if port == 'all':
                # target, all - specific device and all ports
                if device in self._com_devices.keys():
                    for each_port in self._com_devices[device]:
                        self._route_com_msg_to_device_controllers(device, each_port, key, val)
                if device in self._xb_devices.keys():
                    for each_port in self._xb_devices[device]:
                        self._route_xb_msg_to_device_controllers(device, each_port, key, val)
            else:
                # target, target - send to a specific device and specific port
                self._route_com_msg_to_device_controllers(device, port, key, val)
                self._route_xb_msg_to_device_controllers(device, port, key, val)

    def _route_com_msg_to_device_controllers(self, device, port, key, val):
        if device in self._com_devices and port in self._com_devices[device].keys() and device != 'dongle':
            socket: Serial = self._com_devices[device][port]
            self._device_controllers[device].parse_command(socket, key, val)

    def _route_xb_msg_to_device_controllers(self, device, port, key, val):
        if device in self._xb_devices and port in self._xb_devices[device].keys():
            socket: RemoteRaw802Device = self._xb_devices[device][port]
            for com in self._com_devices['dongle']:
                self._device_controllers[device].parse_command(socket, key, val, self._com_devices['dongle'][com])
                break