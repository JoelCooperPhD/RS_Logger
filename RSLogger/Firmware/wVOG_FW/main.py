from wVOG import controller
from uasyncio import run

serial = pyb.USB_VCP()

def run_wvog():
    wvog = controller.WirelessVOG(serial)
    run(wvog.update())

if __name__ is '__main__':
    run_wvog()