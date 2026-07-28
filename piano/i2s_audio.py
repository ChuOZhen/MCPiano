"""
i2s_audio.py - MAX98357A I2S 功放驱动（预初始化 + 样本缓存 + 后台线程）

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

优化点：
- __init__ 时一次性初始化 I2S，play_tone/stop 不再重建/销毁对象。
- 按频率缓存正弦波样本，避免每次重新生成。
- 后台线程持续喂数据，实现按下即发、释放即停的连续音。
"""

import math
import time
import _thread
from machine import I2S, Pin

SAMPLE_RATE = 16000
BITS = 16
CHANNELS = I2S.MONO

# 每个频率缓存的目标样本数（约 100ms 音频，保证 I2S 不断流）
TONE_SAMPLES = 1600

# I2S 内部 DMA 缓冲区大小（字节），应大于单次写入的 buffer，避免断流
IBUF_BYTES = TONE_SAMPLES * 2 * 4

BCLK_GPIO = 16
LRCK_GPIO = 17
DIN_GPIO = 25

# 默认音量（0.0 ~ 1.0），避免削顶
DEFAULT_VOLUME = 0.5


class I2SAudio:
    """MAX98357A I2S 功放驱动，预初始化，支持连续音与静音。"""

    def __init__(self, volume=DEFAULT_VOLUME):
        self.volume = volume
        self._i2s = None
        self._tone_buffer = None
        self._silence = bytearray(TONE_SAMPLES * 2)
        self._cache = {}
        self._stop_flag = True
        self._lock = _thread.allocate_lock()
        self._audio_thread = None
        self._init_i2s()
        self._start_audio_thread()

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
                ibuf=IBUF_BYTES,
            )
        except Exception as e:
            raise RuntimeError(
                "I2S 初始化失败：{} (BCLK=GPIO{}, LRCK=GPIO{}, DIN=GPIO{})".format(
                    e, BCLK_GPIO, LRCK_GPIO, DIN_GPIO)
            )

    def _generate_buffer(self, freq):
        """生成 freq 对应的 16-bit 单声道正弦波 PCM 数据并缓存。"""
        if freq in self._cache:
            return self._cache[freq]

        # 生成整数个完整周期，使缓冲区循环播放时首尾相位连续，避免咔嗒/断续
        period = SAMPLE_RATE / freq
        cycles = max(1, int(TONE_SAMPLES / period))
        n_samples = int(round(cycles * period))

        buf = bytearray(n_samples * 2)
        scale = 32767 * self.volume

        for i in range(n_samples):
            value = int(scale * math.sin(2 * math.pi * freq * i / SAMPLE_RATE))
            if value > 32767:
                value = 32767
            elif value < -32768:
                value = -32768
            buf[i * 2] = value & 0xFF
            buf[i * 2 + 1] = (value >> 8) & 0xFF

        data = bytes(buf)
        self._cache[freq] = data
        return data

    def _audio_loop(self):
        """后台音频循环：持续写入当前 tone buffer 或静音。"""
        while True:
            try:
                self._lock.acquire()
                playing = not self._stop_flag and self._tone_buffer is not None
                buf = self._tone_buffer
                self._lock.release()

                if playing and buf is not None:
                    self._i2s.write(buf)
                else:
                    self._i2s.write(self._silence)

                # 让出 GIL，避免后台线程独占 CPU；1ms 足够且不易断流
                time.sleep_ms(1)
            except Exception:
                # 防止 I2S 异常导致后台线程退出
                time.sleep_ms(10)

    def _start_audio_thread(self):
        """启动后台音频线程。"""
        self._audio_thread = _thread.start_new_thread(self._audio_loop, ())

    def play_tone(self, freq):
        """切换到指定频率持续播放（非阻塞）。"""
        if freq <= 0:
            return
        buf = self._generate_buffer(freq)

        self._lock.acquire()
        try:
            self._tone_buffer = buf
            self._stop_flag = False
        finally:
            self._lock.release()

    def stop(self):
        """停止发声（不销毁 I2S 对象）。"""
        self._lock.acquire()
        try:
            self._stop_flag = True
            self._tone_buffer = None
        finally:
            self._lock.release()

    def __del__(self):
        self.stop()
