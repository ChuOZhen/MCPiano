"""
main.py - MCPiano 入口 — 低延迟主循环

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- 音阶键：GPIO23/22/21/19/18/14/12 → do/re/mi/fa/sol/la/si
- 功能键：GPIO34(八度+), GPIO35(八度-)
- LED 直驱：3.3V → LED → 330Ω → 按键 → GND（GPIO 仅做输入）
- I2S 功放：MAX98357A, BCLK=GPIO16, LRC=GPIO17, DIN=GPIO25
"""

from piano import Piano
import time


def main():
    piano = Piano()
    print("MCPiano 就绪！按下琴键（LED 由硬件直驱）")

    # 主循环：5ms 轮询
    try:
        while True:
            piano.tick()
            time.sleep_ms(5)
    except KeyboardInterrupt:
        piano.close()
        print("\nMCPiano 已停止")


if __name__ == '__main__':
    main()
