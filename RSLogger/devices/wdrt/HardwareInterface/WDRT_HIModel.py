import asyncio
from digi.xbee.devices import XBeeDevice, RemoteRaw802Device, TransmitException


class WDRTModel:
    def __init__(self):
        self.xcvr = None
        self.devices = None


    def data_record(self):
        asyncio.create_task(self.write_msg(f'dta_rcd>'))

    def data_pause(self):
        asyncio.create_task(self.write_msg(f'dta_pse>'))

    def config_request(self, unit_id):
        asyncio.create_task(self.write_msg(f'get_cfg>',  self.get_unit(unit_id)))

    def set_rtc(self, time_str):
        asyncio.create_task(self.write_msg(f'set_rtc>{time_str}'))

    def get_battery(self, unit_id):
        asyncio.create_task(self.write_msg("get_bat>",  self.get_unit(unit_id)))

    def stim_on(self, unit_id):
        asyncio.create_task(self.write_msg(f'set_stm>1', self.get_unit(unit_id)))

    def stim_off(self, unit_id):
        asyncio.create_task(self.write_msg(f'set_stm>0', self.get_unit(unit_id)))

    def verbose_on(self, unit_id):
        asyncio.create_task(self.write_msg(f'set_vrb>1', self.get_unit(unit_id)))

    def verbose_off(self, unit_id):
        asyncio.create_task(self.write_msg(f'set_vrb>0', self.get_unit(unit_id)))

    def set_iso(self, unit_id):
        asyncio.create_task(self.write_msg(f'set_iso>', self.get_unit(unit_id)))

    def set_custom(self, vals, unit_id):
        asyncio.create_task(self.write_msg(f'set_cfg>{vals}', self.get_unit(unit_id)))

    def get_unit(self, unit_id):
        if unit_id:
            for d in self.devices:
                if unit_id == d.get_node_id():
                    return d

    async def write_msg(self, msg, unit=None):
        self.xcvr: XBeeDevice
        unit: RemoteRaw802Device

        if self.xcvr and self.xcvr.is_open():
            try:
                if unit:
                    self.xcvr.send_data(unit, msg)
                    await asyncio.sleep(.1)
                else:
                    try:
                        for dev in self.devices:
                            self.xcvr.send_data(dev, msg)
                    except Exception as e:
                        print(e)
            except TransmitException:
                pass





