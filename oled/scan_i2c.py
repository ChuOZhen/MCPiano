"""
Minimal I2C bus scanner for OLED debugging.

Scans the SoftI2C bus on GPIO5 (SCL) / GPIO13 (SDA) at 100kHz and prints
any responding device addresses.
"""

from machine import Pin, SoftI2C


SCL_PIN = 5
SDA_PIN = 13
I2C_FREQ = 100000


def scan_i2c():
    """Scan the I2C bus and print found device addresses.

    Enables the ESP32 internal pull-ups on SCL/SDA.  If the OLED module
    does not have its own pull-up resistors, the internal pull-ups may be
    enough for a scan, but external 4.7kΩ pull-ups to 3.3V are recommended
    for reliable operation.
    """
    scl = Pin(SCL_PIN, Pin.IN, Pin.PULL_UP)
    sda = Pin(SDA_PIN, Pin.IN, Pin.PULL_UP)
    i2c = SoftI2C(scl=scl, sda=sda, freq=I2C_FREQ)
    devices = i2c.scan()
    print("I2C scan found devices:", [hex(addr) for addr in devices])
    if 0x3C in devices or 0x3D in devices:
        print("SSD1306 OLED detected.")
    else:
        print("No SSD1306 OLED detected (expected 0x3C or 0x3D).")
        print("Try adding external 4.7kΩ pull-up resistors from SCL/SDA to 3.3V.")


if __name__ == "__main__":
    scan_i2c()
