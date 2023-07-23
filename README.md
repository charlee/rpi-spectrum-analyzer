Spectrum Analyzer with Raspberry Pi Pico
=========================================

I bought some RGB LED screens pretty long ago and decided to make something with them.
And this spectrum analyzer is the result.

See the following video for demo. 

[![Demo video](https://img.youtube.com/vi/qcwmG_PlZZ8/0.jpg)](https://youtu.be/qcwmG_PlZZ8)

## Hardware

See [hardware](hardware/) for details.


## Code for Raspberry Pi Pico

- `pixelmatrix.py`: Pixel matrix driver. It uses PIO to drive the LED matrix.
- `code.py`: The main program. It reads the audio signal from ADC pin, uses FFT to convert the signal to spectrum, and then send it to the LED matrix driver.
- `lib/ds1302.py`: DS1302 RTC driver. It is used to display the time on the LED matrix.
- `setup_rtc.py`: A helper to use DS1302 as the time source.

See [rp2040](rp2040/) for details.