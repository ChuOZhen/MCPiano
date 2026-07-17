"""
main.py - 数字钢琴上电自动运行入口

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- 音阶键：GPIO23/22/21/19/18/14/12 → do/re/mi/fa/sol/la/si
- 功能键：GPIO34(八度+), GPIO35(八度-)
- I2S 功放：MAX98357A, BCLK=GPIO16, LRC=GPIO17, DIN=GPIO25
- LED：GPIO32(绿), GPIO33(红)，低电平点亮
"""

from i2s_audio import I2SAudio
from buttons import ButtonMatrix
from piano import Piano


def main():
    """初始化并运行数字钢琴。"""
    audio = None
    try:
        audio = I2SAudio(volume=0.5)
        buttons = ButtonMatrix(debounce_ms=20)
        piano = Piano(audio, buttons, enable_led=True)
        piano.run()
    except KeyboardInterrupt:
        print("\n用户中断，程序退出")
    except Exception as e:
        print(f"\n运行时错误：{e}")
        raise
    finally:
        if audio is not None:
            audio.stop()


if __name__ == "__main__":
    main()
