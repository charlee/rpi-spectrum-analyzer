#DS1302 Library for CircuitPython
#based on https://github.com/sourceperl/rpi.rtc

import time
import digitalio


class DS1302:
    CLK_DELAY = 5E-6
    
    #Trying a constructor where parameters are passed and not hardcoded
    def __init__(self, clk_pin, data_pin, ce_pin):
        self._clk_pin = clk_pin
        self._data_pin = data_pin
        self._ce_pin = ce_pin
        self._clk_pin.direction = digitalio.Direction.OUTPUT
        self._ce_pin.direction = digitalio.Direction.OUTPUT
        #Turning off write protection
        self._start_tx()
        self._w_byte(0x8e)
        self._w_byte(0x00)
        self._end_tx()
        #Disabling charge mode
        self._start_tx()
        self._w_byte(0x90)
        self._w_byte(0x00)
        self._end_tx()
    
    def _start_tx(self):
        #Setting pins for start of transmission
        self._clk_pin.value = False
        self._ce_pin.value = True
    
    def _end_tx(self):
        #Closing transmission
        self._data_pin.direction = digitalio.Direction.INPUT
        self._clk_pin.value = False
        self._ce_pin.value = False
        
    def _r_byte(self):
        #Reading a byte from the module
        self._data_pin.direction = digitalio.Direction.INPUT
        byte = 0
        for i in range(8):
            #High pulse on CLK pin
            self._clk_pin.value = True
            time.sleep(self.CLK_DELAY)
            self._clk_pin.value = False
            time.sleep(self.CLK_DELAY)
            bit = self._data_pin.value
            byte |= ((2 ** i) * bit)
        return byte
        
    def _w_byte(self, byte):
        self._data_pin.direction = digitalio.Direction.OUTPUT
        for _ in range(8):
            self._clk_pin.value = False
            time.sleep(self.CLK_DELAY)
            self._data_pin.value = byte & 0x01
            byte >>= 1
            self._clk_pin.value = True
            time.sleep(self.CLK_DELAY)
    
    def read_ram(self):
        # Not yet implemented
        pass
    
    def write_ram(self):
        # Not yet implemented
        pass
        
        
    def read_datetime(self):
        self._start_tx()
        self._w_byte(0xbf)
        byte_l = []
        for _ in range(7):
            byte_l.append(self._r_byte())
        self._end_tx()
        second = ((byte_l[0] & 0x70) >> 4) * 10 + (byte_l[0] & 0x0f)
        minute = ((byte_l[1] & 0x70) >> 4) * 10 + (byte_l[1] & 0x0f)
        hour = ((byte_l[2] & 0x30) >> 4) * 10 + (byte_l[2] & 0x0f)
        day = ((byte_l[3] & 0x30) >> 4) * 10 + (byte_l[3] & 0x0f)
        month = ((byte_l[4] & 0x10) >> 4) * 10 + (byte_l[4] & 0x0f)
        year = ((byte_l[6] & 0xf0) >> 4) * 10 + (byte_l[6] & 0x0f) + 2000
        return time.struct_time((year, month, day, hour, minute, second, 0, -1, -1))
    
    def write_datetime(self, dt):
        byte_l = [0] * 9
        byte_l[0] = (dt.tm_sec // 10) << 4 | dt.tm_sec % 10
        byte_l[1] = (dt.tm_min // 10) << 4 | dt.tm_min % 10
        byte_l[2] = (dt.tm_hour // 10) << 4 | dt.tm_hour % 10
        byte_l[3] = (dt.tm_mday // 10) << 4 | dt.tm_mday % 10
        byte_l[4] = (dt.tm_mon // 10) << 4 | dt.tm_mon % 10
        byte_l[5] = 0
        byte_l[6] = (((dt.tm_year-2000) // 10) << 4) | (dt.tm_year-2000) % 10
        self._start_tx()
        self._w_byte(0xbe)
        for byte in byte_l:
            self._w_byte(byte)
        self._end_tx()