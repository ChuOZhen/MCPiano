"""
SSD1306 OLED display test for MCPiano.

Uses the bundled ``ssd1306`` driver over SoftI2C on GPIO5 (SCL) and GPIO13
(SDA).  The OLED module is powered from the 5V rail.

If the board reports ``ImportError: no module named 'ssd1306'``, copy
``lib/ssd1306.py`` to the device first::

    mpremote connect /dev/ttyACM0 cp lib/ssd1306.py :lib/ssd1306.py
"""

import time
from machine import Pin, SoftI2C

try:
    import ssd1306
except ImportError as exc:
    print("ERROR: ssd1306 driver not found on the board.")
    print("Copy lib/ssd1306.py to the device:")
    print("  mpremote connect /dev/ttyACM0 cp lib/ssd1306.py :lib/ssd1306.py")
    raise exc


OLED_WIDTH = 128
OLED_HEIGHT = 64
SCL_PIN = 5
SDA_PIN = 13
I2C_FREQ = 100000
TEST_DELAY_S = 1.5


def init_oled():
    """Initialize SoftI2C and SSD1306 OLED.

    Scans the I2C bus first, then tries the common SSD1306 addresses
    ``0x3C`` and ``0x3D``.

    Returns:
        tuple: (oled, i2c, addr) where ``oled`` is the SSD1306 instance,
        ``i2c`` is the SoftI2C bus instance, and ``addr`` is the used
        I2C address.

    Raises:
        OSError: if no SSD1306 device responds on the I2C bus.
    """
    i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
    scan = i2c.scan()
    print(f"I2C scan found devices: {[hex(a) for a in scan]}")

    candidates = [0x3C, 0x3D]
    for addr in candidates:
        if addr in scan:
            try:
                oled = ssd1306.SSD1306_I2C(
                    OLED_WIDTH, OLED_HEIGHT, i2c, addr=addr
                )
                return oled, i2c, addr
            except OSError:
                continue

    raise OSError(
        "SSD1306 not found at 0x3C or 0x3D; "
        "check wiring (SCL=GPIO5, SDA=GPIO13) and power."
    )


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
    addr = None
    try:
        oled, i2c, addr = init_oled()
        print(f"OLED initialized on I2C addr {hex(addr)}")

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
        print("Check wiring (SCL=GPIO5, SDA=GPIO13), power, and I2C address.")
    finally:
        if oled is not None:
            oled.fill(0)
            oled.show()
        if i2c is not None:
            i2c.deinit()
        print("OLED resources released.")


if __name__ == "__main__":
    run_tests()
