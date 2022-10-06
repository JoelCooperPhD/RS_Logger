import asyncio
from time import sleep

import serial
from serial import SerialException
from threading import Thread
from queue import SimpleQueue


class DRTController:
    def __init__(self, q_out):
        self._q_out: SimpleQueue = q_out

        self._file_path = None

        # results
        self._clicks = dict()
        self._results = dict()
        self._cond_name = ""
        
    def parse_command(self, serial_device, key, val=None):

        if   key == 'init'         : pass
        elif key == 'close'        : pass
        elif key == 'start'        : self._send(serial_device, 'exp_start')
        elif key == 'stop'         : self._send(serial_device, 'exp_stop')

        elif key == 'stim_on'      : self._send(serial_device, 'stim_on')
        elif key == 'stim_off'     : self._send(serial_device, 'stim_off')

        elif key == 'get_config'   : self._send(serial_device, 'get_config')
        elif key == 'get_lowerISI' : self._send(serial_device, 'get_lowerISI')
        elif key == 'set_lowerISI' : self._send(serial_device, 'set_lowerISI', val)
        elif key == 'get_upperISI' : self._send(serial_device, 'get_upperISI')
        elif key == 'set_upperISI' : self._send(serial_device, 'set_upperISI', val)
        elif key == 'get_stimDur'  : self._send(serial_device, 'get_stimDur')
        elif key == 'set_stimDur'  : self._send(serial_device, 'set_stimDur', val)
        elif key == 'get_intensity': self._send(serial_device, 'get_intensity')
        elif key == 'set_intensity': self._send(serial_device, 'set_intensity', val)
        elif key == 'get_name'     : self._send(serial_device, 'get_name')

        elif key == 'iso'          : self.set_iso(serial_device)

        elif key == 'fpath'        : self._file_path = val

        elif key == 'clk'          : self._clicks[serial_device.port] = val
        elif key == 'trl'          : self._results[serial_device.port] = val
        elif key == 'end'          : self._log_results(serial_device.port)

        elif key == 'stm'          :
            if val == '1'          : self._clicks[serial_device.port] = 0

        elif key == 'cond'         : self._cond_name = val

    def set_iso(self, serial):
        self._send(serial, 'set_lowerISI', 3000)
        self._send(serial, 'set_upperISI', 5000)
        self._send(serial, 'set_stimDur', 1000)
        self._send(serial, 'set_intensity', 255)

    def _log_results(self, com):
        if len(self._clicks):
            d = self._results[com].split(',')

            data = f'{d[0]},{d[1]},{d[2]},{self._clicks[com]},{d[3]}'

            packet = f'drt_{com},{self._cond_name},{data}'

            def _write(_path, _results):
                try:
                    with open(_path, 'a') as writer:
                        writer.write(_results + '\n')
                except (PermissionError, FileNotFoundError):
                    pass

            file_path = f"{self._file_path}/drt.txt"
            t = Thread(target=_write, args=(file_path, packet))
            t.start()

    @staticmethod
    def _send(serial_conn, cmd, val=None):
        def _send_2_com(_cmd):
            serial_conn.write(_cmd)

        if val: cmd = f'{cmd} {val}\n\r'
        else  : cmd = f'{cmd}\n\r'

        t = Thread(target=_send_2_com, args=(str.encode(cmd),))
        t.start()
