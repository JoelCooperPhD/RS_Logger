from asyncio import create_task, sleep
from digi.xbee.devices import XBeeDevice, RemoteRaw802Device, TransmitException


class WVOGModel:
    def __init__(self):
        self.xcvr = None
        self.devices = None

    def cmd_passer(self, unit_id, arg, val=None):
        create_task(self._write_msg(f'{arg}:{val}', self._get_unit(unit_id)))

    def _get_unit(self, unit_id):
        if unit_id:
            for d in self.devices:
                if unit_id == d.get_node_id():
                    return d

    async def _write_msg(self, msg, unit=None):
        self.xcvr: XBeeDevice
        unit: RemoteRaw802Device

        if self.xcvr and self.xcvr.is_open():
            try:
                if unit:
                    self.xcvr.send_data(unit, msg)
                    await sleep(0.0001)
                else:
                    try:
                        for dev in self.devices:
                            self.xcvr.send_data(dev, msg)
                    except Exception as e:
                        print(e)
            except TransmitException:
                pass





