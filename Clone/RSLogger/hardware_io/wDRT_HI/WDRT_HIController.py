from asyncio import sleep
from queue import SimpleQueue
from serial import Serial
from threading import Thread
from time import gmtime

from digi.xbee.devices import XBeeDevice, RemoteRaw802Device


class WDRTController:
    def __init__(self, q_out):
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

        elif key == "fpath"  : self._file_path = f"{val}/DRT.txt"

        elif 'cond' in key   :
            self._cond_name = val.split(':')[0]

        elif 'dta' in key    : self._log_to_csv(socket, val)

    def _set_rtc(self, socket, xcvr):
        tt = gmtime()
        time_gmt = f"{tt[0]},{tt[1]},{tt[2]},{tt[6]},{tt[3]},{tt[4]},{tt[5]},123"
        self._send(socket, f'set_rtc>{time_gmt}', xcvr)

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

            packet = f"DRT_{unit_id},{self._cond_name},{data}"
            file_path = f"{self._file_path}"
            t = Thread(target=_write, args=(file_path, packet))
            t.start()

    def _send(self, socket, cmd, xcvr: XBeeDevice = None):
        if xcvr:
            socket: RemoteRaw802Device
            xcvr.send_data(socket, cmd)
        else:
            socket.write(str.encode(f'{cmd}\n'))
