from pyb import RTC, MMCard
import os
import micropython

micropython.alloc_emergency_exception_buf(100)


class MMC:
    def __init__(self):
        self.mmc = MMCard()
        self.mount_mmc()
        self.fname = None
        self.rtc = RTC()

    def mount_mmc(self):
        try:
            os.mount(self.mmc, '/mmc')
        except:
            print("Failed to mount")

    def init(self, header):
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
        with open(self.fname, 'a') as outfile:
            outfile.write(data)
