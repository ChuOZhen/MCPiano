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
    """Scan the I2C bus and print found device addresses."""
    i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=I2C_FREQ)
    try:
        devices = i2c.scan()
        print("I2C scan found devices:", [hex(addr) for addr in devices])
        if 0x3C in devices or 0x3D in devices:
            print("SSD1306 OLED detected.")
        else:
            print("No SSD1306 OLED detected (expected 0x3C or 0x3D).")
    finally:
        i2c.deinit()


if __name__ == "__main__":
    scan_i2c()
