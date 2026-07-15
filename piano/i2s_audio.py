"""
i2s_audio.py - MAX98357A I2S 功放驱动模块

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- 功放模块：MAX98357A（5V 供电，D 类 I2S 数字功放）
- I2S GPIO 映射：
    BCLK -> GPIO16
    LRCK (WS) -> GPIO17
    DIN -> GPIO25
- 音频格式：16-bit 单声道，采样率 16 kHz
- 供电：MAX98357A VIN 接开发板 5V，GND 与 ESP32 共地
- 控制：SD_MODE 接 VIN 使能，GAIN 接 VIN（本模块 GND=高增益、VIN=正常增益）

注意：本模块只操作 I2S 相关 GPIO（16/17/25），不触碰 LED/按键 GPIO。
"""

import math
from machine import I2S, Pin

SAMPLE_RATE = 16000
BITS = 16
CHANNELS = I2S.MONO
BUFFER_SIZE = 40000

NOTES = {
    'C4': 262,
    'D4': 294,
    'E4': 330,
    'F4': 349,
    'G4': 392,
    'A4': 440,
    'B4': 494,
    'C5': 523,
}


class I2SAudio:
    """MAX98357A I2S 功放驱动类。"""

    def __init__(self, bclk_gpio=16, lrck_gpio=17, din_gpio=25):
        """
        初始化 I2S 音频输出。

        Args:
            bclk_gpio: I2S 位时钟引脚，默认 GPIO16。
            lrck_gpio: I2S 帧时钟（WS）引脚，默认 GPIO17。
            din_gpio: I2S 数据输入引脚，默认 GPIO25。
        """
        self._audio = None
        self._bclk_gpio = bclk_gpio
        self._lrck_gpio = lrck_gpio
        self._din_gpio = din_gpio

        try:
            self._audio = I2S(
                0,
                sck=Pin(bclk_gpio),
                ws=Pin(lrck_gpio),
                sd=Pin(din_gpio),
                mode=I2S.TX,
                bits=BITS,
                format=CHANNELS,
                rate=SAMPLE_RATE,
                ibuf=BUFFER_SIZE,
            )
        except Exception as e:
            raise RuntimeError(
                "I2S 初始化失败：BCLK=GPIO{}, LRCK=GPIO{}, DIN=GPIO{}。错误：{}".format(
                    bclk_gpio, lrck_gpio, din_gpio, e
                )
            )

    def _generate_samples(self, freq, duration_ms, volume):
        """
        生成指定频率和时长的 16-bit 单声道正弦波 PCM 数据。

        Args:
            freq: 频率（Hz）。
            duration_ms: 时长（毫秒）。
            volume: 音量（0.0 ~ 1.0）。

        Returns:
            bytearray: PCM 样本缓冲区。
        """
        num_samples = SAMPLE_RATE * duration_ms // 1000
        buf = bytearray(num_samples * 2)

        for i in range(num_samples):
            value = int(
                32767 * volume
                * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
            )
            if value > 32767:
                value = 32767
            elif value < -32768:
                value = -32768
            buf[i * 2] = value & 0xFF
            buf[i * 2 + 1] = (value >> 8) & 0xFF

        return buf

    def play_tone(self, freq, duration_ms, volume=0.5):
        """
        播放指定频率的正弦波音调。

        Args:
            freq: 频率（Hz），必须大于 0。
            duration_ms: 播放时长（毫秒）。
            volume: 音量，范围 0.0 ~ 1.0，默认 0.5。
        """
        if not isinstance(freq, int) or freq <= 0:
            raise ValueError("freq 必须是正整数")
        if not (0.0 <= volume <= 1.0):
            raise ValueError("volume 必须在 0.0 ~ 1.0 之间")

        try:
            samples = self._generate_samples(freq, duration_ms, volume)
            self._audio.write(samples)
        except Exception as e:
            raise RuntimeError(
                "播放音调失败：freq={}Hz, duration={}ms, GPIO{}(DIN) 输出错误：{}".format(
                    freq, duration_ms, self._din_gpio, e
                )
            )

    def play_note(self, note_name, duration_ms=300):
        """
        按音符名称播放音调。

        Args:
            note_name: 音符名称，如 'C4'、'G4'。
            duration_ms: 播放时长（毫秒），默认 300。
        """
        note_name = note_name.upper()
        if note_name not in NOTES:
            raise ValueError(f"未知音符：{note_name}，可用：{list(NOTES.keys())}")

        self.play_tone(NOTES[note_name], duration_ms)

    def stop(self):
        """停止输出并释放 I2S 资源。"""
        if self._audio is not None:
            try:
                self._audio.deinit()
            except Exception:
                pass
            self._audio = None
