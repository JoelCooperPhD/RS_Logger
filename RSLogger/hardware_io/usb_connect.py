import asyncio
import serial
from digi.xbee.devices import XBeeDevice
from serial.tools.list_ports import comports
from asyncio import get_running_loop

from serial.serialutil import SerialException

BAUD = 921600

ids = {'sftDRT': {'pid': 'F055', 'vid': '9800'},
       'sDRT'  : {'pid': '801F', 'vid': '239A'},
       'wDRT'  : {'pid': '1111' , 'vid': 'F056' },
       'sVOG'  : {'pid': '16C0', 'vid': '0483'},
       'wVOG'  : {'pid': '08AE' , 'vid': 'F057' },
       'dongle': {'pid': '6015', 'vid': '0403'}}


async def scan_usb_ports(found_device_callback):
    old_ports = list()
    known_rs_devices = dict()
    connected_rs_devices = dict()

    while 1:
        try:
            loop = get_running_loop()
            new_ports = await loop.run_in_executor(None, comports)
            len_diff = len(new_ports) - len(old_ports)

            # Any change? Updated known device list
            if len_diff != 0:
                known_rs_devices.clear()
                for p in new_ports:
                    for name in ids:
                        if ids[name]['vid'] in p[2]:
                            device_name = [name, ids[name]['vid'], ids[name]['pid']]
                            known_rs_devices[p[0]] = device_name
                            pass
                old_ports = new_ports
                await asyncio.sleep(.2)

                # If a device was plugged in, connect to it and add it to the dict of connected devices.
                to_add = {k: known_rs_devices[k] for k in
                          set(known_rs_devices) - set(connected_rs_devices)}

                if to_add:
                    for port in to_add:
                        try:
                            if known_rs_devices[port][0] == 'dongle':
                                connected_rs_devices[port] = [to_add[port][0], XBeeDevice(port, BAUD)]
                            else:
                                connected_rs_devices[port] = [to_add[port][0], serial.Serial(port, BAUD, timeout=.5)]
                        except SerialException:
                            pass

                # If a device was unplugged, remove it from the connected list of rs devices
                to_remove = {k: connected_rs_devices[k] for k in
                             set(connected_rs_devices) - set(known_rs_devices)}

                if to_remove:
                    for port in to_remove:
                        if connected_rs_devices[port][0] == 'dongle':
                            pass
                        else:
                            connected_rs_devices[port][1].close()

                        connected_rs_devices.pop(port)

                # Update the hi controller with any changes
                found_device_callback(connected_rs_devices)

        except RuntimeError:
            pass
        await asyncio.sleep(.1)
