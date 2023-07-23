import array
import rp2pio
import adafruit_pioasm
import adafruit_framebuf as framebuf

class Color:
    BLACK   = (0, 0, 0)
    RED     = (1, 0, 0)
    GREEN   = (0, 1, 0)
    BLUE    = (0, 0, 1)
    YELLOW  = (1, 1, 0)
    CYAN    = (0, 1, 1)
    MAGENTA = (1, 0, 1)
    WHITE   = (1, 1, 1)
    
class Dimension:
    SIZE_X = 4
    SIZE_Y = 1
    MATRIX_SIZE = 8
    WIDTH = MATRIX_SIZE * SIZE_X
    HEIGHT = MATRIX_SIZE * SIZE_Y
    
    
class PSFormat:
    """Pixel format for the pixel screen.
    """

    @staticmethod
    def set_pixel(framebuf, x, y, color):
        index = (y * framebuf.width + x) // 8
        offset = x & 0x07
        framebuf.buf[index] = (framebuf.buf[index] & ~(0x80 >> offset)) | ((color & 0x01) << (7 - offset))

    @staticmethod
    def get_pixel(framebuf, x, y):
        index = (y * framebuf.width + x) // 8
        offset = x & 0x07
        return (framebuf.buf[index] >> (7 - offset)) & 0x01

    @staticmethod
    def fill(framebuf, color):
        if color:
            fill = 0xff
        else:
            fill = 0x00

        for i in range(len(framebuf.buf)):
            framebuf.buf[i] = fill

    @staticmethod
    def fill_rect(framebuf, x, y, width, height, color):
        for _x in range(x, x + width):
            offset = _x & 0x07
            for _y in range(y, y + height):
                index = (_y * framebuf.width + _x) // 8
                if color:
                    framebuf.buf[index] |= 0x80 >> offset
                else:
                    framebuf.buf[index] &= ~(0x80 >> offset)


class PixelScreenFrameBuf:
    """The FrameBuf for the 32x8 pixel screen.
    """

    def __init__(self):
        bufsize = int(Dimension.WIDTH / 8 * Dimension.HEIGHT)
        
        # since the LED matrx used by the screen shares one resistor among all R/G/B LEDs,
        # we won't be able to light R with G or B due to R-LED has a way smaller voltage drop than G/B.
        # we have to use scanning to show R and G/B alternatively to simulate colors.
        self._buf_r = bytearray(bufsize)
        self.fb_r = framebuf.FrameBuffer(self._buf_r, Dimension.WIDTH, Dimension.HEIGHT)
        self._buf_g = bytearray(bufsize)
        self.fb_g = framebuf.FrameBuffer(self._buf_g, Dimension.WIDTH, Dimension.HEIGHT)
        self._buf_b = bytearray(bufsize)
        self.fb_b = framebuf.FrameBuffer(self._buf_b, Dimension.WIDTH, Dimension.HEIGHT)
        
        self.fb_r.format = PSFormat()
        self.fb_g.format = PSFormat()
        self.fb_b.format = PSFormat()


    def get_data(self):
        bufsize = int(Dimension.WIDTH / 8 * Dimension.HEIGHT)
        data = array.array('L', [0] * bufsize * 2)

        for i in range(bufsize):
            # chip select byte
            cs = (i // Dimension.SIZE_X) % Dimension.MATRIX_SIZE
            data[i] = (0b10000000 >> cs) << 24 | 0x00ffff00 | (self._buf_r[i] ^ 0xff)

        for i in range(bufsize):
            # chip select byte
            cs = (i // Dimension.SIZE_X) % Dimension.MATRIX_SIZE
            data[bufsize + i] = (0b10000000 >> cs) << 24 | 0x000000ff | (self._buf_g[i] ^ 0xff) << 16 | (self._buf_b[i] ^ 0xff) << 8

        return data

    def pixel(self, x, y, color):
        """Set the pixel at position (x, y) to the given color.
        """
        self.fb_r.pixel(x, y, color[0])
        self.fb_g.pixel(x, y, color[1])
        self.fb_b.pixel(x, y, color[2])
        
    def fill(self, color):
        """Fill the screen with the given color.
        """
        self.fb_r.fill(color[0])
        self.fb_g.fill(color[1])
        self.fb_b.fill(color[2])

    def rect(self, x, y, width, height, color):
        self.fb_r.rect(x, y, width, height, color[0])
        self.fb_g.rect(x, y, width, height, color[1])
        self.fb_b.rect(x, y, width, height, color[2])

    def fill_rect(self, x, y, width, height, color):
        self.fb_r.fill_rect(x, y, width, height, color[0])
        self.fb_g.fill_rect(x, y, width, height, color[1])
        self.fb_b.fill_rect(x, y, width, height, color[2])

    def hline(self, x, y, width, color):
        self.fb_r.hline(x, y, width, color[0])
        self.fb_g.hline(x, y, width, color[1])
        self.fb_b.hline(x, y, width, color[2])

    def vline(self, x, y, height, color):
        self.fb_r.vline(x, y, height, color[0])
        self.fb_g.vline(x, y, height, color[1])
        self.fb_b.vline(x, y, height, color[2])

    def line(self, x1, y1, x2, y2, color):
        self.fb_r.line(x1, y1, x2, y2, color[0])
        self.fb_g.line(x1, y1, x2, y2, color[1])
        self.fb_b.line(x1, y1, x2, y2, color[2])

    def circle(self, center_x, center_y, radius, color):
        self.fb_r.circle(center_x, center_y, radius, color[0])
        self.fb_g.circle(center_x, center_y, radius, color[1])
        self.fb_b.circle(center_x, center_y, radius, color[2])

    def scroll(self, dx, dy):
        self.fb_r.scroll(dx, dy)
        self.fb_g.scroll(dx, dy)
        self.fb_b.scroll(dx, dy)

    def text(self, string, x, y, color):
        self.fb_r.text(string, x, y, color[0])
        self.fb_g.text(string, x, y, color[1])
        self.fb_b.text(string, x, y, color[2])



"""
PIO assmebly code for driving the 4-LED-Matrix screen
"""
quad_led_matrix_spi = """
    .program quad_led_matrix_spi
    .side_set 1

    set pins, 0x7
    set x, 31
loop1:
    out pins, 1       side 0
    jmp x--, loop1    side 1
    
    set pins, 0xb
    set x, 31
loop2:
    out pins, 1       side 0
    jmp x--, loop2    side 1

    set pins, 0xd
    set x, 31
loop3:
    out pins, 1       side 0
    jmp x--, loop3    side 1

    set pins, 0xe
    set x, 31
loop4:
    out pins, 1       side 0
    jmp x--, loop4    side 1
"""


class PixelScreen:
    def __init__(self, clk, mosi, first_cs, freq=1_000_000):
        assembled = adafruit_pioasm.assemble(quad_led_matrix_spi)
        self.sm = rp2pio.StateMachine(assembled, frequency=freq,
                                      first_out_pin=mosi,
                                      first_set_pin=first_cs,
                                      set_pin_count=Dimension.SIZE_X,
                                      first_sideset_pin=clk,
                                      auto_pull=True,
                                     )

        self.fb = PixelScreenFrameBuf()

    def show(self):
        data = self.fb.get_data()
        self.sm.background_write(loop=data)


# test code
if __name__ == '__main__':
    import board
    import time
    screen = PixelScreen(clk=board.GP2, mosi=board.GP3, first_cs=board.GP10)
    x = 1
    y = 1
    
    while True:
        screen.fb.fill(Color.BLACK)
        screen.fb.text('Hello, world', x, 0, Color.RED)
#         screen.fb.pixel(x, y, Color.RED)
#         screen.fb.fill_rect(0, 0, x, y, Color.GREEN)
#         screen.fb.line(0, 0, x, y, Color.YELLOW)

        # color test
#         screen.fb.fill_rect(0, 0, 8, 4, Color.RED)
#         screen.fb.fill_rect(8, 0, 8, 4, Color.GREEN)
#         screen.fb.fill_rect(16, 0, 8, 4, Color.BLUE)
#         screen.fb.fill_rect(24, 0, 8, 4, Color.BLACK)
#         screen.fb.fill_rect(0, 4, 8, 4, Color.YELLOW)
#         screen.fb.fill_rect(8, 4, 8, 4, Color.CYAN)
#         screen.fb.fill_rect(16, 4, 8, 4, Color.MAGENTA)
#         screen.fb.fill_rect(24, 4, 8, 4, Color.WHITE)
#         
        screen.show()
        time.sleep(0.5)
        x -= 1



        




