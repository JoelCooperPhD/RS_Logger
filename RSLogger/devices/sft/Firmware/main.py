from uasyncio import run
from SFT import drt_sft

serial = pyb.USB_VCP()
drt = drt_sft.SystemsFactorialTechnology(serial)

run(drt.run())