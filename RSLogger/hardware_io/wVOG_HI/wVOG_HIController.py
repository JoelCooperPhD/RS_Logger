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

    def __init__(self, q_out: SimpleQueue, debug: bool = True):
        """
        Initializes the wVOGController hardware controller object.

        Args:
            q_out (SimpleQueue): Queue to which messages can be sent.
            debug (bool, optional): Whether to print debug information. Defaults to True.
        """
        self._debug = debug
        if self._debug: print(f'{time_ns()} wVOGController.__init__')

        self._q_2_ui: SimpleQueue = q_out
        # self._XB_connect = XBeeMessage()

        # Writer
        self._file_path = ''
        self._cond_name = ''

    ####################################################################################################################
    # PARSE INCOMING COMMANDS

    def parse_command(self, socket, key, val: Optional[str] = None, xcvr: Optional[XBeeDevice] = None) -> None:
        """
        Parses and executes the given command. Delegates the handling of the command to
        different methods based on the type and value of the command.

        Args:
            socket (RemoteRaw802Device or Serial): The device to send the command to.
            key (Union[str, bytes]): The command key.
            val (str, optional): The value associated with the command key. Defaults to None.
            xcvr (XBeeDevice, optional): The XBeeDevice to use to send the command. If not provided, socket's write method is used. Defaults to None.
        """
        if self._debug: print(f'{time_ns()} wVOGController.parse_command {key}, {val}, {xcvr}')

        if isinstance(key, str):
            self._handle_string_command(socket, key, val, xcvr)
        elif isinstance(key, bytes):
            self._handle_key_bytes(socket, key, val)

    def _handle_string_command(self, socket, key: str, val: Optional[str] = None,
                               xcvr: Optional[XBeeDevice] = None) -> None:
        """
        Handles the command when it is a string. If the command is present in `device_commands` or `exp_commands`,
        it is sent to the given socket using the _send method. If the command is 'fpath', the file path for logging is updated.

        Args:
            socket (RemoteRaw802Device or Serial): The device to send the command to.
            key (str): The command key.
            val (str, optional): The value associated with the command key. Defaults to None.
            xcvr (XBeeDevice, optional): The XBeeDevice to use to send the command. If not provided, socket's write method is used. Defaults to None.
        """
        if self._debug: print(f'{time_ns()} wVOGController._handle_string_command {socket.port} {key}, {val}, {xcvr}')

        if key in self.DEVICE_COMMANDS:
            self._send(socket, f'{self.DEVICE_COMMANDS[key]}{val}', xcvr)
        elif 'cond' in key:
            self._cond_name = val.split(':')[0]
        elif key == "fpath":
            self._file_path = f"{val}/{self.LOG_FILE_PATH_TEMPLATE}"

    def _handle_key_bytes(self, socket, key: bytes, val: Optional[str] = None) -> None:
        """
        Handle the command when the key is of bytes type. If 'cfg' is in key,
        a new configuration is to be handled. If 'cond' is in key, the condition name is updated.
        If 'dta' is in key, the data is logged to a CSV file.

        Args:
            key (bytes): The command key in bytes, which will be decoded to utf-8 string for processing.
            socket (RemoteRaw802Device or Serial): The device to which the command will be sent.
            val (str, optional): The value associated with the command key. Defaults to None.
        """
        if self._debug: print(f'{time_ns()} wVOGController._handle_key_bytes {key}, {socket.port}, {val}')

        key = key.decode('utf-8')
        if 'cfg' in key:
            self._q_2_ui.put(f'wVOG>{socket.port}>{key}')

        elif key.startswith('dta>'):
            key, s = key.split('>')
            self._log_to_csv(socket.port, f'{val}{s}')

    ####################################################################################################################
    # WRITE DATA TO FILE

    def _write(self, _path: str, _results: str) -> None:
        """
        Writes data to a file at a given path. If the file does not exist, it also writes a header.
        Intended to be called from a thread spawned in _log_to_csv method.
        If a PermissionError or FileNotFoundError occurs, it logs the error message.

        Args:
            _path (str): The path of the file to write to.
            _results (str): The data to write to the file.
        """
        if self._debug: print(f'{time_ns()} wVOGController._write {_path} {_results}')

        try:
            header = None
            if not isfile(_path):
                header = 'Device ID, Label, Unix time in UTC, Trial Number, Shutter Open, Shutter Closed, Shutter Total,' \
                         'Transition A B or X, Battery SOC, Device Unix time in UTC'
            with open(_path, 'a') as writer:
                if header:
                    writer.write(header + '\n')
                writer.write(_results)
        except (PermissionError, FileNotFoundError) as e:
            print(f"Error when writing to file {_path}: {str(e)}")

    def _log_to_csv(self, unit_id, data: str) -> None:
        """
        Formats the data for logging and starts a thread to write the data to a csv file.
        The actual writing is done by the _write method.

        If unit_id is a RemoteRaw802Device, it extracts the node_id as the unit_id.
        If unit_id is a Serial, it uses the port as the unit_id.

        Args:
            unit_id (Union[str, RemoteRaw802Device, Serial]): The unit id of the device.
            data (str): The data to log.
        """
        if self._debug: print(f'{time_ns()} wVOGController._log_to_csv {unit_id} {data}')

        if self._file_path:
            if isinstance(unit_id, RemoteRaw802Device):
                unit_id = unit_id.get_node_id().split('_')[1]
            elif isinstance(unit_id, Serial):
                unit_id: Serial
                unit_id = unit_id.port

            packet = f"VOG_{unit_id},{self._cond_name},{data}"
            file_path = f"{self._file_path}"
            t = Thread(target=self._write, args=(file_path, packet))
            t.start()

    ####################################################################################################################
    # SEND RESULTS TO DEVICE OVER SERIAL AND XBEE TRANSCEIVER

    def _send(self, socket: Union[RemoteRaw802Device, Serial], cmd: str, xcvr: Optional[XBeeDevice] = None) -> None:
        """
        Sends a command to a device. If a XBeeDevice is provided, it uses the XBeeDevice's send_data method.
        Otherwise, it uses the socket's write method.

        Args:
            socket (Union[RemoteRaw802Device, Serial]): The device to send the command to.
            cmd (str): The command to send.
            xcvr (XBeeDevice, optional): The XBeeDevice to use to send the command. If not provided, socket's write method is used. Defaults to None.
        """
        if self._debug: print(f'{time_ns()} wVOGController._send {socket.port} {cmd} {xcvr}')

        if xcvr:
            self._send_with_xcvr(socket, cmd, xcvr)
        else:
            self._send_over_serial(socket, cmd)

    def _send_with_xcvr(self, socket: RemoteRaw802Device, cmd: str, xcvr: XBeeDevice) -> None:
        """
        Sends a command to a device using the XBeeDevice's send_data method.

        Args:
            socket (RemoteRaw802Device): The device to send the command to.
            cmd (str): The command to send.
            xcvr (XBeeDevice): The XBeeDevice to use to send the command.
        """
        if self._debug: print(f'{time_ns()} wVOGController._send_with_xcvr {socket} {cmd} {xcvr}')

        if not isinstance(socket, RemoteRaw802Device):
            raise TypeError('Socket must be of type RemoteRaw802Device when xcvr is provided.')
        xcvr.send_data(socket, cmd)

    def _send_over_serial(self, socket: Serial, cmd: str) -> None:
        """
        Sends a command to a device using the socket's write method.

        Args:
            socket (Serial): The device to send the command to.
            cmd (str): The command to send.
        """
        if self._debug: print(f'{time_ns()} wVOGController._send_over_serial {socket.port} {cmd}')

        if not isinstance(socket, Serial):
            raise TypeError('Socket must be of type Serial when xcvr is not provided.')
        socket.write(str.encode(f'{cmd}\n'))



