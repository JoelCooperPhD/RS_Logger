from asyncio import sleep
from queue import SimpleQueue
from serial import Serial
from threading import Thread
import re
from time import time_ns

from digi.xbee.devices import XBeeDevice, RemoteRaw802Device


class wDRTController:
    def __init__(self, q_out, debug=False):
        self._debug = debug
        if self._debug: print("WDRT_HIController.__init__")

        self._q_2_ui: SimpleQueue = q_out

        # Writer
        self._file_path = ''
        self._cond_name = ''

    # Queue Monitor
    def parse_command(self, socket, key, val=None, xcvr=None):
        # COMMANDS FOR wDRT
        if   key == "get_cfg": self._send(socket, 'get_cfg>', xcvr)
        elif key == "get_bat": self._send(socket, 'get_bat>', xcvr)
        elif key == "stm_on" : self._send(socket, 'set_stm>1', xcvr)
        elif key == "stm_off": self._send(socket, 'set_stm>0', xcvr)
        elif key == "set_cfg": self._send(socket, f'set_cfg>{val}', xcvr)
        elif key == "set_iso": self._send(socket, 'set_iso>', xcvr)
        elif key == "vrb_on" : self._send(socket, 'set_vrb>1', xcvr)
        elif key == "vrb_off": self._send(socket, 'set_vrb>0', xcvr)

        elif key == "set_rtc": self._send(socket, f'set_rtc>{val}', xcvr)


        # PARENT COMMANDS
        elif key == "start"  : self._send(socket, 'dta_rcd>', xcvr)
        elif key == "stop"   : self._send(socket, 'dta_pse>', xcvr)

        elif key == "fpath"  : self._set_file_path(socket, f"{val}/DRT.txt")

        elif 'cond' in key   :
            self._cond_name = val.split(':')[0]

        elif 'dta' in key    : self._log_to_csv(socket, val)

    def _threaded_write(self, fpath, data):
        try:
            with open(fpath, 'a') as outfile:
                outfile.writelines(data)
        except (PermissionError, OSError):
            sleep(0.05)
            self._threaded_write(fpath, data)
            print("Permission Error, retrying")

    def _log_to_csv(self, unit_id, data):
        def _write(_path, _results):
            try:
                with open(_path, 'a') as writer:
                    writer.write(_results + '\n')
            except (PermissionError, FileNotFoundError):
                print(f'path: {_path}, data: {_results}')

        if self._file_path:
            if isinstance(unit_id, RemoteRaw802Device):
                match = re.match(r"(\w+)\s*[_ ]?\s*(\d+)", unit_id.get_node_id())
                unit_id = match.groups()[1]
            elif isinstance(unit_id, Serial):
                unit_id: Serial
                unit_id = unit_id.port

            packet = f"DRT_{unit_id},{self._cond_name},{data}"
            file_path = f"{self._file_path}"
            t = Thread(target=_write, args=(file_path, packet))
            t.start()

    def _set_file_path(self, unit_id, path):
        self._file_path = f"{path}"
        headers = "Device_Unit,Label,Data_Receive_sec.ms, Block_ms, Trial, Reaction Time, Responses, UTC, Battery"
        try:
            with open(path, 'a') as writer:
                writer.write(headers + '\n')
        except (PermissionError, FileNotFoundError):
            if self._debug: print(f'{time_ns()} WDRT_HIController {path}, {headers}')

    def _send(self, socket, cmd, xcvr: XBeeDevice = None):
        if xcvr:
            socket: RemoteRaw802Device
            xcvr.send_data(socket, cmd)
        else:
            socket.write(str.encode(f'{cmd}\n'))
