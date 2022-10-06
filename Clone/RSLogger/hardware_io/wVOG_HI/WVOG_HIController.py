from asyncio import sleep
from queue import SimpleQueue
from serial import Serial
from threading import Thread

from digi.xbee.devices import XBeeDevice, RemoteRaw802Device, TransmitException


class WVOGController:
    def __init__(self, q_out):
        self._q_2_ui: SimpleQueue = q_out

        # self._XB_connect = XBeeMessage()

        # Writer
        self._file_path = ''
        self._cond_name = ''

    # Queue Monitor
    def parse_command(self, socket, key, val=None, xcvr=None):
        # COMMANDS FOR wDRT

        if   key == "get_cfg": self._send(socket, 'cfg>', xcvr)
        elif key == "set_cfg":
            self._send(socket, f'set>{val}', xcvr)
        elif key == "get_bat": self._send(socket, 'bat>', xcvr)
        elif key == "a_on" : self._send(socket, 'a>1', xcvr)
        elif key == "a_off": self._send(socket, 'a>0', xcvr)
        elif key == "b_on" : self._send(socket, 'b>1', xcvr)
        elif key == "b_off": self._send(socket, 'b>0', xcvr)
        elif key == "ab_on": self._send(socket, 'x>1', xcvr)
        elif key == "ab_off": self._send(socket, 'x>0', xcvr)
        elif key == "get_rtc": self._send(socket, 'rtc', xcvr)
        elif key == "set_rtc": self._send(socket, f'rtc>{val}', xcvr)

        # PARENT COMMANDS
        elif key == "init": self._send(socket, 'exp>1', xcvr)
        elif key == "close": self._send(socket, 'exp>0', xcvr)
        elif key == "start": self._send(socket, 'trl>1', xcvr)
        elif key == "stop": self._send(socket, 'trl>0', xcvr)

        elif key == "fpath"  : self._file_path = f"{val}/VOG.txt"

        elif 'cond' in key   :
            self._cond_name = val.split(':')[0]

        elif 'dta' in key    :
            self._log_to_csv(socket, val)

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
                pass

        if self._file_path:
            if isinstance(unit_id, RemoteRaw802Device):
                unit_id = unit_id.get_node_id().split('_')[1]
            elif isinstance(unit_id, Serial):
                unit_id: Serial
                unit_id = unit_id.port

            packet = f"VOG_{unit_id},{self._cond_name},{data}"
            file_path = f"{self._file_path}"
            t = Thread(target=_write, args=(file_path, packet))
            t.start()

    @staticmethod
    def _send(socket, cmd, xcvr: XBeeDevice = None):
        try:
            if xcvr:
                socket: RemoteRaw802Device
                xcvr.send_data(socket, cmd)
            else:
                socket.write(str.encode(f'{cmd}\n'))
        except (PermissionError, TransmitException) as e:
            print(e)
