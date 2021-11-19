from wDRT import wdrt
from uasyncio import run

serial = pyb.USB_VCP()

def run_wdrt():
    wdrt_ = wdrt.wDRT(serial)
    run(wdrt_.update())


if __name__ is '__main__':
    run_wdrt()