import time
import board
import digitalio
import rtc
import ds1302

# Define the clock, data and enable pins
clkpin = digitalio.DigitalInOut(board.GP16)
datapin = digitalio.DigitalInOut(board.GP17)
cepin = digitalio.DigitalInOut(board.GP18)

# Instantiate the ds1302 class
ds1302 = ds1302.DS1302(clkpin,datapin,cepin)

# Redefine the RTC class to link with the ds1302
class RTC(object):
    @property
    def datetime(self):
        return ds1302.read_datetime()

# Instantiate the rtc class and set the time source
r = RTC()
rtc.set_time_source(r)


# Run this file directly to setup the RTC time.
if __name__ == '__main__':
    tm = time.localtime()
    ds1302.write_datetime(tm)
    rtc_tm = ds1302.read_datetime()
    print(rtc_tm)