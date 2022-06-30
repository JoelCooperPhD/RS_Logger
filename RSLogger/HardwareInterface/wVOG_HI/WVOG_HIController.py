from asyncio import create_task, sleep
from RSLogger.HardwareInterface.wVOG_HI import WVOG_HIResults, WVOG_HIModel, WVOG_HIxbee
from queue import SimpleQueue
from digi.xbee.devices import XBeeMessage, RemoteRaw802Device
from time import gmtime


class WVOGController:
    def __init__(self, q_out, q_in):
        self._q_out: SimpleQueue = q_out
        self._q_in: SimpleQueue = q_in

        self._XB_connect = WVOG_HIxbee.ConnectionManager()
        self._HW_interface = WVOG_HIModel.WVOGModel()

        # Writer
        self.data = WVOG_HIResults.Master()
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

            # Send current time to all connected wVOG units
            tt = gmtime()
            time_gmt = f"{tt[0]},{tt[1]},{tt[2]},{tt[6]},{tt[3]},{tt[4]},{tt[5]},123"
            self._HW_interface.cmd_passer('rtc', time_gmt)

            # Pass list of devices to wVOG UI
            dvc_str = ','.join([d.get_node_id() for d in devices])
            self._q_out.put(f"ui_wVOG>devices>{dvc_str}")

    async def _handle_messages_from_xcvr(self):
        # wVOG Commands read in from the xbee network device
        # This method is registered as a callback with the xbee library
        while True:
            msg: XBeeMessage = await self._XB_connect.xb_msg_q.get()
            dev: RemoteRaw802Device = msg.remote_device

            cmd, args = msg.data.decode().split(":")
            n_id = dev.get_node_id()

            if cmd == 'dta':
                create_task(self.data.write(n_id, self._cond_name, args, msg.timestamp))

            self._q_out.put(f"ui_wVOG>{cmd}>{n_id},{args}")

    # Queue Monitor
    async def _handle_messages_between_threads(self):
        while True:
            while not self._q_in.empty():
                msg = self._q_in.get()
                if self._HW_interface.xcvr and self._HW_interface.devices:
                    cmd = msg.split('>')[1]
                    args = msg.split('>')[2:]

                    # PARENT COMMANDS
                    if cmd == "fpath":
                        self.data.fpath = f"{args[0]}/wVOG.txt"
                    elif cmd == "init":
                        self._XB_connect.stop_network_scan()
                        self._HW_interface.cmd_passer(self._HW_interface.devices, 'exp', '1')
                    elif cmd == "close":
                        self._XB_connect.start_network_scan()
                        self._HW_interface.cmd_passer(self._HW_interface.devices, 'exp', '0')
                    elif cmd == "start":
                        self._HW_interface.cmd_passer(self._HW_interface, 'trl', '1')
                    elif cmd == "stop":
                        self._HW_interface.cmd_passer(self._HW_interface, 'trl', '0')

                    # VOG COMMANDS -> wVOG
                    elif cmd in ['rtc', 'bty', 'x', 'a', 'b', 'drk', 'clr',
                                 'cls', 'dbc', 'opn', 'srt', 'dta', 'typ']:
                        self._HW_interface.cmd_passer(self._HW_interface.devices, cmd, args)

                    else:
                        print(f"wVOG HI_Controller _queue_monitor command not handled: {cmd}")

            await sleep(0.0001)
