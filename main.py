import board
from supervisor import ticks_ms, ticks_diff
from kmk.kmk_keyboard import KMKKeyboard
from kmk.keys import KC
from kmk.scanners import DiodeOrientation
from kmk.modules.encoder import EncoderHandler
from kmk.modules.layers import Layers
from kmk.extensions.media_keys import MediaKeys
from kmk.extensions.RGB import RGB, AnimationModes
from kmk.extensions.display import Display, TextEntry
from kmk.extensions.display.ssd1306 import SSD1306



keyboard = KMKKeyboard()
layers = Layers()


# The PCB has six switches arranged as two rows by three columns
keyboard.row_pins = (board.D3, board.D6)
keyboard.col_pins = (board.D9, board.D10, board.D8)
keyboard.diode_orientation = DiodeOrientation.ROW2COL


class ProfileEncoderHandler(EncoderHandler):
    """Keep volume on turns; short press mutes, long press changes profile."""

    HOLD_MS = 700

    def __init__(self):
        super().__init__()
        self.press_started = None
        self.long_press_triggered = False

    def _switch_profile(self, keyboard):
        current = keyboard.active_layers[0]
        next_profile = (current + 1) % 3
        keyboard.active_layers.clear()
        layers.activate_layer(keyboard, next_profile)

    def on_button_do(self, keyboard, encoder_id, state):
        if state['is_pressed']:
            self.press_started = ticks_ms()
            self.long_press_triggered = False
            return

        if self.press_started is None:
            return

        if not self.long_press_triggered:
            keyboard.tap_key(KC.MUTE)

        self.press_started = None
        self.long_press_triggered = False

    def before_matrix_scan(self, keyboard):
        update = super().before_matrix_scan(keyboard)
        if self.press_started is not None and not self.long_press_triggered:
            held_ms = ticks_diff(ticks_ms(), self.press_started)
            if held_ms >= self.HOLD_MS:
                self._switch_profile(keyboard)
                self.long_press_triggered = True
        return update


encoder_handler = ProfileEncoderHandler()
keyboard.modules = [layers, encoder_handler]
keyboard.extensions.append(MediaKeys())

# Encoder A, B, and push switch
encoder_handler.pins = ((board.D0, board.D1, board.D2, False),)
encoder_handler.map = [
    ((KC.VOLD, KC.VOLU, KC.NO),),
    ((KC.VOLD, KC.VOLU, KC.NO),),
    ((KC.VOLD, KC.VOLU, KC.NO),),
]


# RGB data
rgb = RGB(
    pixel_pin=board.D7,
    num_pixels=14,
    val_limit=100,
    val_default=60,
    hue_default=0,
    sat_default=255,
    animation_mode=AnimationModes.STATIC,
)
keyboard.extensions.append(rgb)


PROFILE_NAMES = ('EVERYDAY', 'POPULAR', 'RGB & PAD')


class ProfileDisplay(Display):
    """Show the current profile and animate a short sliding arrow on changes."""

    ANIMATION_MS = 560
    FRAME_MS = 70

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_layer = None
        self._transition_start = None
        self._last_frame = -1

    def render(self, layer):
        profile_number = layer + 1
        profile_name = PROFILE_NAMES[layer]
        entries = [
            TextEntry(text='PROFILE {} / 3'.format(profile_number), x=0, y=0),
            TextEntry(text=profile_name, x=0, y=12),
        ]

        if self._transition_start is not None:
            elapsed = ticks_diff(ticks_ms(), self._transition_start)
            if elapsed < self.ANIMATION_MS:
                frame = elapsed // self.FRAME_MS
                arrow_x = min(frame * 16, 112)
                entries.append(TextEntry(text='>', x=arrow_x, y=24))

        self.entries = entries
        super().render(layer)

    def before_matrix_scan(self, keyboard):
        super().before_matrix_scan(keyboard)
        active_layer = keyboard.active_layers[0]

        if self._last_layer is None:
            self._last_layer = active_layer
        elif active_layer != self._last_layer:
            self._last_layer = active_layer
            self._transition_start = ticks_ms()
            self._last_frame = -1
            self.render(active_layer)

        if self._transition_start is not None:
            elapsed = ticks_diff(ticks_ms(), self._transition_start)
            if elapsed >= self.ANIMATION_MS:
                self._transition_start = None
                self.render(active_layer)
            else:
                frame = elapsed // self.FRAME_MS
                if frame != self._last_frame:
                    self._last_frame = frame
                    self.render(active_layer)


#The OLED display pins
i2c = board.I2C()
display_driver = SSD1306(i2c=i2c, device_address=0x3C)
display = ProfileDisplay(
    display=display_driver,
    width=128,
    height=32,
    brightness=0.8,
    dim_time=0,
    off_time=0,
)
keyboard.extensions.append(display)


# Profile 1: everyday editing and navigation shortcuts.
# Profile 2: popular browser and Windows shortcuts.
# Profile 3: RGB controls (toggle, hue, brightness, and effects).
keyboard.keymap = [
    [
        KC.LCTL(KC.C), KC.LCTL(KC.V), KC.LCTL(KC.X),
        KC.LCTL(KC.Z), KC.LCTL(KC.Y), KC.LCTL(KC.A),
    ],
    [
        KC.LCTL(KC.S), KC.LCTL(KC.F), KC.LCTL(KC.T),
        KC.LCTL(KC.W), KC.LCTL(KC.LSHIFT(KC.T)),
        KC.LGUI(KC.LSHIFT(KC.S)),
    ],
    [
        KC.RGB_TOG, KC.RGB_HUD, KC.RGB_HUI,
        KC.RGB_VAD, KC.RGB_VAI, KC.RGB_MODE_RAINBOW,
    ],
]


if __name__ == '__main__':
    keyboard.go()
