from asyncio import create_task, sleep
from RSLogger.HardwareInterface.wDRT_HI import WDRT_HIResults, WDRT_HIModel, WDRT_HIxbee
from queue import SimpleQueue
from digi.xbee.devices import XBeeMessage, RemoteRaw802Device
from time import gmtime


class WDRTController:
    def __init__(self, q_out, q_in):
        self._q_out: SimpleQueue = q_out
        self._q_in: SimpleQueue = q_in

        self._XB_connect = WDRT_HIxbee.ConnectionManager()
        self._HW_interface = WDRT_HIModel.WDRTModel()

        # Writer
        self.data = WDRT_HIResults.Master()
        self._cond_name = ''

    def run(self):
        create_task(self._sync_xcvr())
        create_task(self._sync_network())
        create_task(self._handle_messages_from_xcvr())
        create_task(self._handle_messages_between_threads())

    # Xbee connect
    async def _sync_xcvr(self):
        while True:
            self._HW_interface.xcvr = await self._XB_connect.attached_xcvr_q.get()
            if self._HW_interface.xcvr:
                self._XB_connect.start_network_scan()

    async def _sync_network(self):
        while True:
            devices = await self._XB_connect.networked_devices_q.get()

            self._HW_interface.devices = devices
            tt = gmtime()
            time_gmt = f"{tt[0]},{tt[1]},{tt[2]},{tt[6]},{tt[3]},{tt[4]},{tt[5]},123"
            self._HW_interface.set_rtc(time_gmt)
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

            # -- cfg: New configuration
            if cmd == 'cfg':
                self._q_out.put(f"ui_wdrt>cfg>{args} {n_id}")
                print(f'Config {n_id}: {args}')
            # -- stm: Stimulus change notification
            elif cmd == 'stm':
                self._q_out.put(f"ui_wdrt>stm>{args} {n_id}")
            # -- dta: End of trial data frame
            elif cmd == 'dta':
                create_task(self.data.write(n_id, self._cond_name, args, msg.timestamp))
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
            while not self._q_in.empty():
                msg = self._q_in.get()
                if self._HW_interface.xcvr and self._HW_interface.devices:
                    cmd = msg.split('>')[1]
                    args = msg.split('>')[2:]

                    # DRT COMMANDS -> wDRT
                    if cmd == "get_cfg":
                        self._HW_interface.config_request(args[0])
                    elif cmd == "get_bat":
                        self._HW_interface.get_battery(args[0])
                    elif cmd == "stm_on":
                        self._HW_interface.stim_on(args[0])
                    elif cmd == "stm_off":
                        self._HW_interface.stim_off(args[0])
                    elif cmd == "set_cfg":
                        args = args[0].split(',')
                        self._HW_interface.set_custom(args[:-1], args[-1])
                    elif cmd == "set_iso":
                        self._HW_interface.set_iso(args[0])
                    elif cmd == "net_scn":
                        self._XB_connect.clear_network()
                        self._HW_interface.devices.clear()
                    elif cmd == "vrb_on":
                        self._HW_interface.verbose_on(args[0])
                    elif cmd == "vrb_off":
                        self._HW_interface.verbose_off(args[0])

                    # PARENT COMMANDS
                    elif cmd == "fpath":
                        self.data.fpath = f"{args[0]}/wDRT.txt"
                    elif cmd == "init":
                        self._XB_connect.stop_network_scan()
                    elif cmd == "close":
                        self._XB_connect.start_network_scan()
                    elif cmd == "start":
                        self._HW_interface.data_record()
                    elif cmd == "stop":
                        self._HW_interface.data_pause()
                    elif 'cond' in cmd:
                        self._cond_name = cmd.split(':')[1]
                    else:
                        print(f"wdrt HI_Controller _queue_monitor command not handled: {cmd}")

            await sleep(0.0001)
