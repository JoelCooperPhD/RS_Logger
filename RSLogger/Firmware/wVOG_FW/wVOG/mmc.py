from pyb import RTC, MMCard
import os
import micropython
from uasyncio import create_task, sleep
from pyb import usb_mode

micropython.alloc_emergency_exception_buf(100)


class MMC:
    def __init__(self, delayed_broadcast):
        self._broadcast = delayed_broadcast
        self.mmc = MMCard()
        self.mmc_present = False
        
        if 'MSC' in usb_mode():
            self.mmc.power(1)

            if self.mmc.info():
                self.fname = None
                self.rtc = RTC()
                
                create_task(self.mount_mmc())
                self.present = True

    async def mount_mmc(self):
        while 1:
            if self.mmc.info():
                break
            await sleep(1)
        try:
            os.mount(self.mmc, '/mmc')
            self.mmc_present = True
        except Exception as e:
            print(f'MMC Error: {e}')
            # from utilities import mmc_format
            # mmc_format.mmc_format()
            

    def init(self, header):
        if self.mmc_present:
            max_v = "0"
            rtc = self.rtc.datetime()
            dt = "{}-{}-{}".format(rtc[0], rtc[1], rtc[2])
            for f in os.listdir('/mmc'):
                kv = f.split("_")
                if kv[0].isdigit() and int(kv[0]) >= int(max_v):
                    max_v = str(int(kv[0]) + 1)

            self.fname = "/mmc/{}_{}.txt".format(max_v, dt)
            with open(self.fname, 'w') as outfile:
                outfile.write(header)

    def write(self, data):
        if self.mmc_present:
            with open(self.fname, 'a') as outfile:
                outfile.write(data)