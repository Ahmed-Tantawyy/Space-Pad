import board

from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from kmk.modules.encoder import EncoderHandler
from kmk.extensions.media_keys import MediaKeys
from kmk.extensions.display import Display, ImageEntry
from kmk.extensions.display.ssd1306 import SSD1306

keyboard = KMKKeyboard()



# Key matrix: 2 rows x 3 columns = 6 switches:
keyboard.row_pins = (board.D3, board.D6)
keyboard.col_pins = (board.D9, board.D10, board.D8)
keyboard.diode_orientation = DiodeOrientation.ROW2COL



# Media keys (volume and mute) for the encoder:
keyboard.extensions.append(MediaKeys())

# Rotary encoder: A pin, B pin, button pin, inverted direction, to change the volume and mute:
encoder_handler = EncoderHandler()
keyboard.modules.append(encoder_handler)
encoder_handler.pins = ((board.D0, board.D1, board.D2, False),)
encoder_handler.map = [
    ((KC.VOLD, KC.VOLU, KC.MUTE),),
]



# OLED display:
i2c = board.I2C()
display_driver = SSD1306(i2c=i2c, device_address=0x3C)

display = Display(
    display=display_driver,
    width=128,
    height=32,
    brightness=0.8,
    dim_time=0,   # never dim
    off_time=0,   # never turn off
)

# Show the black hole image full-screen
display.entries = [
    ImageEntry(image="blackhole.bmp", x=0, y=0),
]

keyboard.extensions.append(display)



# The 6 shortcuts:
keyboard.keymap = [
    [
        KC.LCTL(KC.C), KC.LCTL(KC.V), KC.LCTL(KC.X),   # copy, paste, cut
        KC.LCTL(KC.Z), KC.LCTL(KC.Y), KC.LCTL(KC.A),   # undo, redo, select all
    ]
]

if __name__ == '__main__':
    keyboard.go()