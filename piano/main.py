"""
main.py - 9 键数字钢琴入口程序

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- I2S 功放：GPIO16(BCLK), GPIO17(LRCK), GPIO25(DIN)
- 9 个按键：GPIO23/22/21/19/18/14/12/34/35

上电自动进入工作状态，Ctrl+C 安全退出。
"""

import time
from i2s_audio import I2SAudio
from buttons import ButtonMatrix
from piano import Piano


def main():
    """钢琴主程序入口。"""
    audio = None
    try:
        print("🎹 MCPiano 9 键数字钢琴启动")
        audio = I2SAudio()
        buttons = ButtonMatrix()
        piano = Piano(audio, buttons, enable_led=False)

        print("等待按键... 按 Ctrl+C 退出")
        while True:
            piano.tick()
            time.sleep_ms(10)

    except KeyboardInterrupt:
        print("\n👋 用户中断")
    except Exception as e:
        print(f"\n❌ 运行时错误：{e}")
    finally:
        if audio is not None:
            audio.stop()
            print("🔇 I2S 资源已释放")


if __name__ == "__main__":
    main()
