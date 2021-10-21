import asyncio
from RSLogger.devices.wdrt.HardwareInterface import WDRT_HIResults, WDRT_HIxbee, WDRT_HIModel
from queue import SimpleQueue
from digi.xbee.devices import XBeeMessage, RemoteRaw802Device
import time

from RSLogger.devices.common_utilities.HardwareInterface import USBConnect


class WDRTController:
    def __init__(self, q_out, q_in):
        self._q_out: SimpleQueue = q_out
        self._q_in: SimpleQueue = q_in

        self._XB_connect = WDRT_HIxbee.ConnectionManager()
        self._HW_interface = WDRT_HIModel.WDRTModel()

        # Writer
        self.data = WDRT_HIResults.Master()

        # USB Serial Connection
        self._connection_manager = USBConnect.ConnectionManager(name='wdrt', vid='F056', pid='9800')

    def run(self):
        asyncio.create_task(self._connect_event())
        asyncio.create_task(self._connection_manager.update())
        asyncio.create_task(self._sync_xcvr())
        asyncio.create_task(self._sync_network())
        asyncio.create_task(self._handle_messages_from_xcvr())
        asyncio.create_task(self._handle_messages_between_threads())

    # USB Connect
    async def _connect_event(self):
        while 1:
            self._connected_drt_devices = await self._connection_manager.new_connection()
            self._connected_drt_ports = ','.join(list(self._connected_drt_devices.keys()))
            msg = f'ui_wdrt>devices>{self._connected_drt_ports}'
            self._q_out.put(msg)

            if self._connected_drt_devices:
                self._listen_to_connected_drt = True
            else:
                self._listen_to_connected_drt = False

    # Xbee connect
    async def _sync_xcvr(self):
        while True:
            self._HW_interface.xcvr = await self._XB_connect.attached_xcvr_q.get()
            if self._HW_interface.xcvr:
                self._XB_connect.start_network_scan()

    async def _sync_network(self):
        while True:
            devices = await self._XB_connect.networked_devices_q.get()
            tt = time.gmtime()
            time_gmt = f"{tt[0]},{tt[1]},{tt[2]},{tt[6]},{tt[3]},{tt[4]},{tt[5]},123"
            self._HW_interface.set_rtc(time_gmt)
            self._HW_interface.devices = devices
            dvc_str = ','.join([d.get_node_id() for d in devices])
            self._q_out.put(f"ui_wdrt>devices>{dvc_str}")

    async def _handle_messages_from_xcvr(self):
        # wDRT Commands read in from the xbee network device
        # This method is registered as a callback with the xbee library
        while True:
            msg: XBeeMessage = await self._XB_connect.xb_msg_q.get()
            dev: RemoteRaw802Device = msg.remote_device

            cmd, args = msg.data.decode().split(">")
            n_id = dev.get_node_id()

            # print(f"New Message from XB: {cmd}: {args}")

            # -- cfg: New configuration
            if cmd == 'cfg':
                self._q_out.put(f"ui_wdrt>cfg>{args} {n_id}")
            # -- stm: Stimulus change notification
            elif cmd == 'stm':
                self._q_out.put(f"ui_wdrt>stm>{args} {n_id}")
            # -- dta: End of trial data frame
            elif cmd == 'dta':
                asyncio.create_task(self.data.write(n_id, args, msg.timestamp))
                self._q_out.put(f"ui_wdrt>dta>{n_id},{args}")
            # -- dvc: New device string
            elif cmd == 'dvc':
                self._q_out.put(f"ui_wdrt>devices>{args[1:]}")
            # -- bty: New battery information
            elif cmd == 'bty':
                self._q_out.put(f"ui_wdrt>bty>{n_id},{args}")
            # -- rt: New direct RT value
            elif cmd == 'rt':
                self._q_out.put(f"ui_wdrt>rt>{n_id},{args}")
            # -- clk: Click count
            elif cmd == 'clk':
                self._q_out.put(f"ui_wdrt>clk>{n_id},{args}")

            else:
                print(f"wdrt HI_Controller _xb_uart_cb command not handled: {cmd}")

    # Queue Monitor
    async def _handle_messages_between_threads(self):
        while True:
            if self._HW_interface.devices:
                while not self._q_in.empty():
                    msg = self._q_in.get()
                    cmd = msg.split('>')[1]
                    args = msg.split('>')[2:]

                    # DRT COMMANDS -> wDRT
                    # -- get_cfg: Request configuration from wDRT unit
                    if cmd == "get_cfg":
                        self._HW_interface.config_request(args[0])
                    # -- get_bat: Request current battery state from wDRT unit
                    elif cmd == "get_bat":
                        self._HW_interface.get_battery(args[0])
                    # -- stm_on: Request wDRT unit turn on stimulus
                    elif cmd == "stm_on":
                        self._HW_interface.stim_on(args[0])
                    # -- stm_off: Request wDRT unit turn off stimulus
                    elif cmd == "stm_off":
                        self._HW_interface.stim_off(args[0])
                    # -- set_cfg: Pass new configuration to wDRT unit
                    elif cmd == "set_cfg":
                        args = args[0].split(',')
                        self._HW_interface.set_custom(args[:-1], args[-1])
                    # -- set_iso: Request wDRT unit to set configuration to ISO 17488
                    elif cmd == "set_iso":
                        self._HW_interface.set_iso(args[0])
                    # -- net_scn: Clear known devices
                    elif cmd == "net_scn":
                        self._XB_connect.clear_network()
                        self._HW_interface.devices.clear()
                    # -- vrb_on: set hardware to send stim state, button state, and RT information
                    elif cmd == "vrb_on":
                        self._HW_interface.verbose_on(args[0])
                    # -- vrb_off: only send results
                    elif cmd == "vrb_off":
                        self._HW_interface.verbose_off(args[0])

                    # PARENT COMMANDS
                    # -- ctrl.fpath: New file path for saving data
                    elif cmd == "fpath":
                        self.data.fpath = f"{args[0]}/wDRT.txt"
                    # -- ctrl.log_init: Initialize data logger
                    elif cmd == "init":
                        # self._q_out.put("init>")
                        self._XB_connect.stop_network_scan()
                    # -- ctrl.log_close: Finalize wDRT logs
                    elif cmd == "close":
                        # self._q_out.put("close>")
                        self._XB_connect.start_network_scan()
                    # -- ctrl.data_record: Start recording data from wDRT devices
                    elif cmd == "start":
                        self._HW_interface.data_record()
                        # self._q_out.put("record>")
                    # -- ctrl.data_pause: Pause wDRT device data collection
                    elif cmd == "stop":
                        self._HW_interface.data_pause()
                        # self._q_out.put("pause>")
                    else:
                        print(f"wdrt HI_Controller _queue_monitor command not handled: {cmd}")

            await asyncio.sleep(.001)
