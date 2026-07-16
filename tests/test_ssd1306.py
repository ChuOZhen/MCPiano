"""
SSD1306 OLED display test for MCPiano.

Uses the MicroPython built-in ``ssd1306`` driver over SoftI2C on GPIO2 (SCL)
and GPIO4 (SDA).  The OLED module is powered from the 5V rail.
"""

import time
from machine import Pin, SoftI2C
import ssd1306


OLED_WIDTH = 128
OLED_HEIGHT = 64
SCL_PIN = 2
SDA_PIN = 4
I2C_FREQ = 400000
TEST_DELAY_S = 1.5


def init_oled():
    """Initialize SoftI2C and SSD1306 OLED.

    Returns:
        tuple: (oled, i2c) where ``oled`` is the SSD1306 instance and
        ``i2c`` is the SoftI2C bus instance.
    """
    i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
    oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
    return oled, i2c


def test_show_title(oled):
    """Test 1: clear screen and show the project title."""
    oled.fill(0)
    oled.text('MCPiano', 0, 0)
    oled.show()


def test_show_notes(oled):
    """Test 2: display the seven-note scale names line by line."""
    notes = ['do', 're', 'mi', 'fa', 'sol', 'la', 'si']
    oled.fill(0)
    for i, note in enumerate(notes):
        oled.text(note, 0, i * 10)
    oled.show()


def test_dynamic_playback(oled):
    """Test 3: simulate key-press feedback with dynamic playback info."""
    oled.fill(0)
    oled.text('Playing:', 0, 0)
    oled.text('sol (G4)', 0, 16)
    oled.show()


def test_invert(oled):
    """Test 4: invert display colors (optional contrast test)."""
    oled.fill(0)
    oled.text('Invert test', 0, 0)
    oled.show()
    oled.invert(1)
    time.sleep(TEST_DELAY_S)
    oled.invert(0)


def run_tests():
    """Run all OLED display tests in sequence.

    Handles initialization errors gracefully and ensures the I2C bus is
    released in the ``finally`` block.
    """
    oled = None
    i2c = None
    try:
        oled, i2c = init_oled()
        print("OLED initialized on I2C addr 0x3C")

        tests = [
            ("Title: MCPiano", test_show_title),
            ("Scale names", test_show_notes),
            ("Dynamic playback", test_dynamic_playback),
            ("Invert display", test_invert),
        ]

        for name, test in tests:
            print(f"Running: {name}")
            test(oled)
            time.sleep(TEST_DELAY_S)

        print("All OLED tests completed.")
    except OSError as exc:
        print(f"OLED init failed: {exc}")
        print("Check wiring (SCL=GPIO2, SDA=GPIO4) and I2C address.")
        print("Some modules use addr=0x3D instead of default 0x3C.")
    finally:
        if oled is not None:
            oled.fill(0)
            oled.show()
        if i2c is not None:
            i2c.deinit()
        print("OLED resources released.")


if __name__ == "__main__":
    run_tests()
