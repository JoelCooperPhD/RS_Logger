from threading import Thread
from queue import SimpleQueue

import serial.serialutil
from os.path import isfile


class sVOGController:
    def __init__(self, q_2_ui):
        self._q_2_ui: SimpleQueue = q_2_ui

        self._file_path = None

        # results
        self._clicks = '0'
        self._cond_name = ''

    def parse_command(self, serial_device, key, val=None):

        if   key == 'init'            : self._send(serial_device, '>do_expStart|<<')
        elif key == 'close'           : self._send(serial_device, '>do_expStop|<<')
        elif key == 'start'           : self._send(serial_device, '>do_trialStart|<<')
        elif key == 'stop'            : self._send(serial_device, '>do_trialStop|<<')

        elif key == 'fpath'           : self._file_path = val

        elif key == 'do_peekOpen'     : self._send(serial_device, '>do_peekOpen|<<')
        elif key == 'do_peekClose'    : self._send(serial_device, '>do_peekClose|<<')
        elif key == 'get_config'      : self._get_cfg(serial_device)

        elif key == 'nhtsa'           : self._set_cfg_nhtsa(serial_device)

        elif key == 'cond'            : self._cond_name = val

        elif key == 'data'            : self._log_results(serial_device.port, val)

        elif not isinstance(key, bytes):
            if 'cfg' in key             : self._set_cfg(serial_device, key)

        elif isinstance(key, bytes):
            key = key.decode('utf-8')
            for keyword in ['deviceVer', 'configName', 'configMaxOpen', 'configMaxClose',
                            'configDebounce', 'configClickMode', 'configButtonControl', 'stm', 'data']:
                if keyword in key:
                    k, v = key.split('|')
                    self._q_2_ui.put(f'sVOG>{serial_device.port}>{k}>{v}')
                    if keyword == 'data':
                        self._log_results(serial_device.port, f'{val},{v}')
                    break

    def _get_cfg(self, serial_conn):
        for msg in ['get_deviceVer', 'get_configName', 'get_configMaxOpen', 'get_configMaxClose',
                    'get_configDebounce', 'get_configClickMode', 'get_configButtonControl']:
            self._send(serial_conn, f'>{msg}|<<')

    def _set_cfg(self, serial_conn, cmd):
        cmds = ['set_configName', 'set_configMaxOpen', 'set_configMaxClose',
                'set_configDebounce', 'set_configClickMode', 'set_configButtonControl']
        cmd_split = cmd.split(',')[1:]
        for i, msg in enumerate(cmd_split):
            packet = f'>{cmds[i]}|{msg}<<'
            self._send(serial_conn, packet)

    def _set_cfg_nhtsa(self, serial_conn):
        for msg in ['set_lowerISI 3000', 'set_upperISI 5000', 'set_stimDur 1000', 'set_intensity 255']:
            self._send(serial_conn, f'{msg}')

    def _log_results(self, com, data):
        packet = f'vog_{com},{self._cond_name},{data}'

        def _write(_path, _results):
            try:
                header = None
                if not isfile(_path):
                    header = 'Device ID, Label, Unix time in UTC, Trial Number,' \
                             'Shutter Open, Shutter Closed'
                with open(_path, 'a') as writer:
                    if header: writer.write(header + '\n')
                    writer.write(_results)
            except (PermissionError, FileNotFoundError):
                print("Control write error")

        file_path = f"{self._file_path}/sVOG.txt"
        t = Thread(target=_write, args=(file_path, packet))
        t.start()

    @staticmethod
    def _send(serial_conn, cmd, val=None):
        def _send_2_com(_cmd):
            try:
                serial_conn.write(_cmd)
            except serial.serialutil.SerialTimeoutException as e:
                print(f'SVOG HIController: {e}')

        if val: cmd = f'{cmd} {val}\n'
        else  : cmd = f'{cmd}\n'

        t = Thread(target=_send_2_com, args=(str.encode(cmd),))
        t.start()

