import asyncio
from threading import Thread
from queue import SimpleQueue
from os.path import isfile


class sDRTController:
    def __init__(self, q_2_ui):
        self._q_2_ui: SimpleQueue = q_2_ui

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

        elif key == 'stim'         : self._stimulus_toggle(serial_device, val)

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

        elif key == 'iso'          : asyncio.create_task(self.set_iso((serial_device)))

        elif key == 'fpath'        : self._file_path = val
        elif key == 'cond'         : self._cond_name = val

        # Data from device
        elif isinstance(key, bytes):
            key = key.decode('utf-8')
            if   'clk' in key : self._handle_clicks_device_data(serial_device.port, key)
            elif 'trl' in key : self._handle_trial_device_data(serial_device.port, key, val)
            elif 'end' in key : self._handle_end_device_data(serial_device.port)
            elif 'stm' in key : self._handle_stimulus_device_callback(serial_device.port, key)
            elif 'cfg' in key : self._handle_config_device_data(serial_device.port, key)

    def _stimulus_toggle(self, serial_device, val):
        if val == 'on'   : self._send(serial_device, 'stim_on')
        elif val == 'off': self._send(serial_device, 'stim_off')

    def _handle_trial_device_data(self, port, key, val):
        k, v = key.strip().split('>')
        v = f'{val},{v}'
        self._results[port] = v
        self._q_2_ui.put(f'sDRT>{port}>{k}>{v}')

    def _handle_clicks_device_data(self, port, key):
        k, v = key.strip().split('>')
        self._clicks[port] = v
        self._q_2_ui.put(f'sDRT>{port}>{k}>{v}')

    def _handle_end_device_data(self, port):
        self._log_results(port)

    def _handle_stimulus_device_callback(self, port, key):
        k, v = key.strip().split('>')
        self._q_2_ui.put(f'sDRT>{port}>{k}>{v}')

    def _handle_config_device_data(self, port, key):
        k, v = key.strip().split('>')
        self._q_2_ui.put(f'sDRT>{port}>{k}>{v}')

    async def set_iso(self, serial):
        self._send(serial, 'set_lowerISI', 3000)
        await asyncio.sleep(.05)
        self._send(serial, 'set_upperISI', 5000)
        await asyncio.sleep(.05)
        self._send(serial, 'set_stimDur', 1000)
        await asyncio.sleep(.05)
        self._send(serial, 'set_intensity', 255)

    def _log_results(self, com):
        if self._file_path:
            d = self._results[com].split(',')
            if d[2] == '-1':
                self._clicks[com] = 0

            data = f'{d[0]},{d[1]},{d[2]},{self._clicks[com]},{d[3]}'

            packet = f'sDRT_{com},{self._cond_name},{data}'

            def _write(_path, _results):
                try:
                    header = None
                    if not isfile(_path):
                        header = 'Device ID, Label, Unix time in UTC, Milliseconds Since Record, Trial Number, ' \
                                 'Responses, Reaction Time'

                    with open(_path, 'a') as writer:
                        if header: writer.write(header + '\n')
                        writer.write(_results + '\n')
                except (PermissionError, FileNotFoundError) as e:
                    print(f'sDRT_HIController._log_results: {e}')

            file_path = f"{self._file_path}/sDRT.txt"
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

