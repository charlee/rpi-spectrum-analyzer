import setup_rtc
import time
import math
import board
import analogio
import array
from math import sqrt
from ulab import numpy as np
import ulab

from pixelmatrix import PixelScreen, Color, Dimension


SIZE_X = 4
SIZE_Y = 1
MATRIX_SIZE = 8
WIDTH = SIZE_X * MATRIX_SIZE
HEIGHT = SIZE_Y * MATRIX_SIZE
SAMPLE_SIZE = WIDTH * 2

NOISE = 5000

MODE_CLOCK = 0
MODE_SPECTRUM = 1
MODE_TEST = 2


adc = analogio.AnalogIn(board.A0)


def sample():
    '''Sample the ADC.'''
    buffer = np.zeros(SAMPLE_SIZE)
    for i in range(SAMPLE_SIZE):
        buffer[i] = adc.value
        time.sleep(0.00001)
    
    # remove DC component
    mean = sum(buffer) / SAMPLE_SIZE
    buffer = buffer - mean
    
    # windowing
    for i in range(SAMPLE_SIZE / 2):
        factor = 0.54 - 0.46 * math.cos(2 * math.pi * i / (SAMPLE_SIZE-1))
        buffer[i] *= factor
        buffer[SAMPLE_SIZE - i - 1] *= factor
    
    
    # compute fft and magnitude
    freqs = ulab.utils.spectrogram(buffer)
    
    # filter noise
    for i in range(len(freqs)):
        if freqs[i] < NOISE:
            freqs[i] = 0
    
    return freqs


screen = PixelScreen(clk=board.GP2, mosi=board.GP3, first_cs=board.GP10)
mode = MODE_CLOCK

mode_switch_counter = 10000

while True:
    screen.fb.fill(Color.BLACK)

    if mode == MODE_CLOCK:
        # test if need to switch mode
        freqs = sample()
        if any(f > 1 for f in freqs):
            mode_switch_counter -= 1000
        if mode_switch_counter <= 0:
            mode = MODE_SPECTRUM
            mode_switch_counter = 10000
        
        # setup clock
        tm = time.localtime()
        s = (time.monotonic_ns() // 500_000_000) % 2
        if s == 1:
            colon = ':'
        else:
            colon = ' '
        
        text = f'{tm.tm_hour:2d}{colon}{tm.tm_min:02d}'
        screen.fb.text(text, 1, 0, Color.GREEN)
        
    elif mode == MODE_SPECTRUM:
        # setup spectrum analyzer
        
        # sample
        freqs = sample()
        
        # test if need to switch mode
        if all(f <= 1 for f in freqs):
            mode_switch_counter -= 100
        if mode_switch_counter <= 0:
            mode = MODE_CLOCK
            mode_switch_counter = 10000
        
        # draw spectrum
        lo, hi = min(freqs), max(freqs)
        hi = max(hi, NOISE)
        freqs = (freqs - lo) * Dimension.HEIGHT / (hi - lo)
        
        for x in range(Dimension.WIDTH):
            f = (freqs[x // 2] + freqs[(x + 1) // 2]) / 2
            for y in range(f):
                if y < 4:
                    color = Color.GREEN
                elif y < 6:
                    color = Color.YELLOW
                else:
                    color = Color.RED
                screen.fb.pixel(x, Dimension.HEIGHT - 1 - y, color)
                
    screen.show()
    
    if mode == MODE_SPECTRUM:
        time.sleep(0.0001)
    else:
        time.sleep(0.1)
