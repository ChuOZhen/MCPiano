"""
i2s_audio.py - MAX98357A I2S 功放驱动

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- 功放模块：MAX98357A
- I2S 接线：
    GPIO16 -> BCLK
    GPIO17 -> LRCK
    GPIO25 -> DIN
    5V -> VIN
    GND -> GND
    5V -> SD_MODE（使能功放，不可悬空）
    5V -> GAIN（本模块 VIN=正常增益；GND=高增益）
"""

import math
import time
from machine import I2S, Pin

SAMPLE_RATE = 16000
BITS = 16
CHANNELS = I2S.MONO
BUFFER_SIZE = 40000

BCLK_GPIO = 16
LRCK_GPIO = 17
DIN_GPIO = 25

# 默认音量（0.0 ~ 1.0），避免削顶
DEFAULT_VOLUME = 0.5


class I2SAudio:
    """MAX98357A I2S 功放驱动，播放 16-bit PCM 正弦波。"""

    def __init__(self, volume=DEFAULT_VOLUME):
        self.volume = volume
        self._i2s = None
        self._init_i2s()

    def _init_i2s(self):
        """初始化 I2S 接口。"""
        try:
            self._i2s = I2S(
                0,
                sck=Pin(BCLK_GPIO),
                ws=Pin(LRCK_GPIO),
                sd=Pin(DIN_GPIO),
                mode=I2S.TX,
                bits=BITS,
                format=CHANNELS,
                rate=SAMPLE_RATE,
                ibuf=BUFFER_SIZE,
            )
        except Exception as e:
            raise RuntimeError(
                "I2S 初始化失败：{} (BCLK=GPIO{}, LRCK=GPIO{}, DIN=GPIO{})".format(
                    e, BCLK_GPIO, LRCK_GPIO, DIN_GPIO)
            )

    def _generate_sine(self, freq, duration_ms):
        """生成 16-bit 单声道正弦波 PCM 数据。"""
        num_samples = SAMPLE_RATE * duration_ms // 1000
        buf = bytearray(num_samples * 2)

        for i in range(num_samples):
            value = int(
                32767 * self.volume *
                math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
            )
            if value > 32767:
                value = 32767
            elif value < -32768:
                value = -32768
            buf[i * 2] = value & 0xFF
            buf[i * 2 + 1] = (value >> 8) & 0xFF

        return buf

    def play_tone(self, freq, duration_ms):
        """播放指定频率的正弦波，持续 duration_ms 毫秒。"""
        if self._i2s is None:
            self._init_i2s()

        samples = self._generate_sine(freq, duration_ms)
        try:
            self._i2s.write(samples)
        except Exception as e:
            raise RuntimeError(
                f"I2S 播放失败：{e} (freq={freq}Hz, duration={duration_ms}ms)"
            )

    def stop(self):
        """停止发声并释放 I2S 资源。"""
        if self._i2s is not None:
            try:
                self._i2s.deinit()
            except Exception:
                pass
            self._i2s = None

    def __del__(self):
        self.stop()
