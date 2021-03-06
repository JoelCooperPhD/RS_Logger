# boot.py -- run on boot-up
# can run arbitrary Python, but best to keep it minimal

import machine
import pyb
pyb.country('US') # ISO 3166-1 Alpha-2 code, eg US, GB, DE, AU
pyb.Pin('EN_3V3').on()
# pyb.usb_mode('VCP+MSC', vid=0xf057, msc=(pyb.MMCard(),)) # act as a serial and a storage device
