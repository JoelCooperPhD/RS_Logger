from queue import SimpleQueue
from serial import Serial
from threading import Thread
from time import time_ns
from typing import Dict, Union, Optional

from digi.xbee.devices import XBeeDevice, RemoteRaw802Device
from os.path import isfile

class wDRTController:
    DEVICE_COMMANDS: Dict[str, str] = {
        "cfg"       : 'cfg>',
        "set"       : 'set>',
        "stm_on"    : 'dev>1',
        "stm_off"   : 'dev>0',
        "iso"       : 'dev>iso',
        "bat"       : 'bat>',
        "set_rtc"   : 'rtc>',

        "init"      : 'exp>1',
        "close"     : 'exp>0',
        "start"     : 'trl>1',
        "stop"      : 'trl>0'
    }
    
    LOG_FILE_PATH_TEMPLATE = "wDRT.txt"
    
    def __init__(self, q_out: SimpleQueue, debug: bool = False):
        self._debug = debug
        if self._debug: print(f'{time_ns()} wDRTController.__init__')

        self._q_2_ui: SimpleQueue = q_out

        # Writer
        self._file_path = ''
        self._cond_name = ''

    ####################################################################################################################
    # PARSE INCOMING COMMANDS

    def parse_command(self, socket, key, val: Optional[str] = None, xcvr: Optional[XBeeDevice] = None) -> None:
        if self._debug: print(f'{time_ns()} wDRTController.parse_command {key}, {val}, {xcvr}')

        if isinstance(key, str):
            self._handle_string_command(socket, key, val, xcvr)
        elif isinstance(key, bytes) or isinstance(key, bytearray):
            self._handle_key_bytes(socket, key, val)

    def _handle_string_command(self, socket, key: str, val: Optional[str] = None,
                               xcvr: Optional[XBeeDevice] = None) -> None:
        if self._debug: print(f'{time_ns()} wDRTController._handle_string_command {socket} {key}, {val}, {xcvr}')

        if key in self.DEVICE_COMMANDS:
            self._send(socket, f'{self.DEVICE_COMMANDS[key]}{val}', xcvr)
        elif 'cond' in key:
            self._cond_name = val.split(':')[0]
        elif key == "fpath":
            self._file_path = f"{val}/{self.LOG_FILE_PATH_TEMPLATE}"

    def _handle_key_bytes(self, socket, key: bytes, val: Optional[str] = None) -> None:
        if self._debug: print(f'{time_ns()} wDRTController._handle_key_bytes {key}, {socket}, {val}')

        device_id = socket.get_node_id() if isinstance(socket, RemoteRaw802Device) else (
            socket.port if isinstance(socket, Serial) else None)

        key = key.decode('utf-8').strip()

        if device_id is not None and any(substring in key for substring in ['cfg', 'stm', 'bty', 'exp', 'trl', 'rt', 'clk']):
            self._q_2_ui.put(f'wDRT>{device_id}>{key}')
        elif key.startswith('dta>'):
            k, s = key.split('>')
            self._log_to_csv(device_id, f'{val},{s}\n')
            self._q_2_ui.put(f'wDRT>{device_id}>{key}')

    def _write(self, _path: str, _results: str) -> None:
        if self._debug: print(f'{time_ns()} wDRTController._write {_path} {_results}')

        try:
            header = None
            if not isfile(_path):
                header = "Device ID, Label, Unix time in UTC, Milliseconds Since Record, Trial Number, Responses, " \
                         "Reaction Time, Battery Percent, Device time in UTC"
            with open(_path, 'a') as writer:
                if header:
                    writer.write(header + '\n')
                writer.write(_results)
        except (PermissionError, FileNotFoundError) as e:
            if self._debug: print(f"Error when writing to file {_path}: {str(e)}")

    def _log_to_csv(self, unit_id, data: str) -> None:
        if self._debug: print(f'{time_ns()} wDRTController._log_to_csv {unit_id} {data}')

        if self._file_path:
            if isinstance(unit_id, RemoteRaw802Device):
                unit_id = unit_id.get_node_id().split('_')[1]
            elif isinstance(unit_id, Serial):
                unit_id: Serial
                unit_id = unit_id.port

            if 'wDRT' not in unit_id:
                unit_id = f'wDRT_{unit_id}'
            packet = f"{unit_id},{self._cond_name},{data}"
            file_path = f"{self._file_path}"
            t = Thread(target=self._write, args=(file_path, packet))
            t.start()

    ####################################################################################################################
    # SEND RESULTS TO DEVICE OVER SERIAL AND XBEE TRANSCEIVER

    def _send(self, socket: Union[RemoteRaw802Device, Serial], cmd: str, xcvr: Optional[XBeeDevice] = None) -> None:
        if self._debug: print(f'{time_ns()} wDRTController._send {socket} {cmd} {xcvr}')

        if isinstance(socket, Serial):
            try:
                socket.write(str.encode(f'{cmd}\n'))
            except PermissionError as e:
                if self._debug: print(f" WDRTController._send ERROR: {e}")
        elif xcvr:
            xcvr.send_data(socket, cmd)
