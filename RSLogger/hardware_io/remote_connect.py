from digi.xbee.devices import XBeeNetwork, NetworkDiscoveryStatus, XBeeMessage, XBeeDevice


class RemoteConnectionManager:
    def __init__(self, scan_cb, msg_cb):
        self._scan_callback = scan_cb
        self._msg_callback = msg_cb
        self._network = None
        self._transceiver = None

    ####################################################
    # Xbee Dongle
    def update(self, transceiver):
        self._transceiver = transceiver
        if not self._transceiver.is_open():
            self._transceiver.open()
            self._transceiver.add_data_received_callback(self._msg_received)

            self.start_network_scan()

    def _msg_received(self, msg: XBeeMessage):
        if msg:
            device_type, dev_id = msg.remote_device.get_node_id().split('_')
            msg_ = msg.data
            self._msg_callback(device_type, dev_id, msg.data, msg.timestamp)

    ####################################################
    # Remote Xbee devices
    def start_network_scan(self):
        if not self._network:
            self._network: XBeeNetwork = self._transceiver.get_network()
            self._network.add_discovery_process_finished_callback(self._add_devices)
        self._network.start_discovery_process()

    def stop_network_scan(self):
        self._network: XBeeNetwork
        self._network.del_discovery_process_finished_callback(self._add_devices)
        self._network.stop_discovery_process()
        self._network = None

    def clear_network(self):
        self.stop_network_scan()
        self.start_network_scan()
        self._network.clear()

    def _add_devices(self, e: NetworkDiscoveryStatus):
        if e.value[1] == "Success":
            devices = self._network.get_devices()
            if devices:
                self._scan_callback(self._network.get_devices())
            else:
                self.start_network_scan()
