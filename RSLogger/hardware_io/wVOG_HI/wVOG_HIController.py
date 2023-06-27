from time import sleep, time_ns
from queue import SimpleQueue
from serial import Serial
from threading import Thread
from typing import Dict, Union, Optional

from digi.xbee.devices import XBeeDevice, RemoteRaw802Device
from os.path import isfile


class wVOGController:
    """Controller for Wireless Visual Occlusion Glasses (wVOG)"""

    DEVICE_COMMANDS: Dict[str, str] = {
        "get_cfg": 'cfg>',
        "set_cfg": 'set>',
        "get_bat": 'bat>',
        "stm_a": 'a>',
        "stm_b": 'b>',
        "stm_x": 'x>',
        "get_rtc": 'rtc',
        "set_rtc": 'rtc>',

        "init": 'exp>1',
        "close": 'exp>0',
        "start": 'trl>1',
        "stop": 'trl>0'
    }

    LOG_FILE_PATH_TEMPLATE = "wVOG.txt"

    def __init__(self, q_out: SimpleQueue, debug: bool = False):
        self._debug = debug
        if self._debug: print(f'{time_ns()} wVOGController.__init__')

        self._q_2_ui: SimpleQueue = q_out

        # Writer
        self._file_path = ''
        self._cond_name = ''

    ####################################################################################################################
    # PARSE INCOMING COMMANDS

    def parse_command(self, socket, key, val: Optional[str] = None, xcvr: Optional[XBeeDevice] = None) -> None:
        if self._debug: print(f'{time_ns()} wVOGController.parse_command {key}, {val}, {xcvr}')

        if isinstance(key, str):
            self._handle_string_command(socket, key, val, xcvr)
        elif isinstance(key, bytes) or isinstance(key, bytearray):
            self._handle_key_bytes(socket, key, val)

    def _handle_string_command(self, socket, key: str, val: Optional[str] = None,
                               xcvr: Optional[XBeeDevice] = None) -> None:
        if self._debug: print(f'{time_ns()} wVOGController._handle_string_command {socket} {key}, {val}, {xcvr}')

        if key in self.DEVICE_COMMANDS:
            self._send(socket, f'{self.DEVICE_COMMANDS[key]}{val}', xcvr)
        elif 'cond' in key:
            self._cond_name = val.split(':')[0]
        elif key == "fpath":
            self._file_path = f"{val}/{self.LOG_FILE_PATH_TEMPLATE}"

    def _handle_key_bytes(self, socket, key: bytes, val: Optional[str] = None) -> None:
        if self._debug: print(f'{time_ns()} wVOGController._handle_key_bytes {key}, {socket}, {val}')

        device_id = socket.get_node_id() if isinstance(socket, RemoteRaw802Device) else (
            socket.port if isinstance(socket, Serial) else None)

        key = key.decode('utf-8').strip()

        if device_id is not None and any(substring in key for substring in ['cfg', 'stm', 'bty', 'exp', 'trl']):
            self._q_2_ui.put(f'wVOG>{device_id}>{key}')
        elif key.startswith('dta>'):
            k, s = key.split('>')
            self._log_to_csv(device_id, f'{val},{s}\n')
            self._q_2_ui.put(f'wVOG>{device_id}>{key}')

    ####################################################################################################################
    # WRITE DATA TO FILE
    def _write(self, _path: str, _results: str) -> None:
        if self._debug: print(f'{time_ns()} wVOGController._write {_path} {_results}')

        try:
            header = None
            if not isfile(_path):
                header = "Device ID, Label, Unix time in UTC, Trial Number, Shutter Open, Shutter Closed, Shutter Total," \
                         " Transition 0 1 or X,Battery SOC, Device Unix time in UTC"
            with open(_path, 'a') as writer:
                if header:
                    writer.write(header + '\n')
                writer.write(_results)
        except (PermissionError, FileNotFoundError) as e:
            print(f"Error when writing to file {_path}: {str(e)}")

    def _log_to_csv(self, unit_id, data: str) -> None:
        if self._debug: print(f'{time_ns()} wVOGController._log_to_csv {unit_id} {data}')

        if self._file_path:
            if isinstance(unit_id, RemoteRaw802Device):
                unit_id = unit_id.get_node_id().split('_')[1]
            elif isinstance(unit_id, Serial):
                unit_id: Serial
                unit_id = unit_id.port

            if 'wVOG' not in unit_id:
                unit_id = f'wVOG_{unit_id}'
            packet = f"{unit_id},{self._cond_name},{data}"
            file_path = f"{self._file_path}"
            t = Thread(target=self._write, args=(file_path, packet))
            t.start()

    ####################################################################################################################
    # SEND RESULTS TO DEVICE OVER SERIAL AND XBEE TRANSCEIVER

    def _send(self, socket: Union[RemoteRaw802Device, Serial], cmd: str, xcvr: Optional[XBeeDevice] = None) -> None:
        if self._debug: print(f'{time_ns()} wVOGController._send {socket} {cmd} {xcvr}')

        if isinstance(socket, Serial):
            self._send_over_serial(socket, cmd)
        elif xcvr:
            self._send_with_xcvr(socket, cmd, xcvr)

    def _send_with_xcvr(self, socket: RemoteRaw802Device, cmd: str, xcvr: XBeeDevice) -> None:
        if self._debug: print(f'{time_ns()} wVOGController._send_with_xcvr {socket} {cmd} {xcvr}')

        if isinstance(socket, RemoteRaw802Device):
            xcvr.send_data(socket, cmd)

    def _send_over_serial(self, socket: Serial, cmd: str) -> None:
        if self._debug: print(f'{time_ns()} wVOGController._send_over_serial {socket.port} {cmd}')

        if not isinstance(socket, Serial):
            raise TypeError('Socket must be of type Serial when xcvr is not provided.')
        socket.write(str.encode(f'{cmd}\n'))



