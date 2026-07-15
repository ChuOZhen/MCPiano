"""
buttons.py - 9 键数字钢琴按键扫描模块

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- 音阶键：GPIO23/22/21/19/18/14/12 → do/re/mi/fa/sol/la/si
- 功能键：GPIO34(八度+), GPIO35(八度-)
- 电平特性：内部上拉，按下 = 低电平(0)，释放 = 高电平(1)

本模块只负责 GPIO 扫描和去抖，不涉及音频/LED 逻辑。
"""

import time
from machine import Pin

# 7 个音阶键 GPIO，索引 0~6 对应 do~si
NOTE_GPIOS = [23, 22, 21, 19, 18, 14, 12]

# 2 个功能键 GPIO
FUNC_GPIOS = {
    'octave_up': 34,
    'octave_down': 35,
}


class ButtonMatrix:
    """9 键按键矩阵扫描类。"""

    def __init__(self, debounce_ms=20):
        """
        初始化按键扫描。

        Args:
            debounce_ms: 软件去抖时间（毫秒），默认 20。
        """
        self._debounce_ms = debounce_ms

        # 初始化音阶键引脚
        self._note_pins = [
            Pin(gpio, Pin.IN, Pin.PULL_UP) for gpio in NOTE_GPIOS
        ]
        self._note_values = [1] * len(NOTE_GPIOS)
        self._note_times = [0] * len(NOTE_GPIOS)

        # 初始化功能键引脚
        self._func_pins = {
            name: Pin(gpio, Pin.IN, Pin.PULL_UP)
            for name, gpio in FUNC_GPIOS.items()
        }
        self._func_values = {name: 1 for name in FUNC_GPIOS}
        self._func_times = {name: 0 for name in FUNC_GPIOS}

    def _scan_pin(self, pin, last_value, last_time, now):
        """
        扫描单个按键，带边沿检测和去抖。

        Returns:
            (new_value, last_time, pressed): 新的稳定状态、更新时间、是否触发按下事件
        """
        raw = pin.value()
        pressed = False

        if raw != last_value:
            if time.ticks_diff(now, last_time) > self._debounce_ms:
                # 状态稳定下来
                last_value = raw
                last_time = now
                if raw == 0:
                    pressed = True

        return last_value, last_time, pressed

    def scan_all(self):
        """
        扫描所有按键。

        Returns:
            dict: {'notes': [note_idx, ...], 'funcs': [func_name, ...]}
                notes 中保存被按下的音阶索引（0~6）
                funcs 中保存被按下的功能键名称
        """
        events = {'notes': [], 'funcs': []}
        now = time.ticks_ms()

        for idx, pin in enumerate(self._note_pins):
            self._note_values[idx], self._note_times[idx], pressed = \
                self._scan_pin(pin, self._note_values[idx], self._note_times[idx], now)
            if pressed:
                events['notes'].append(idx)

        for name, pin in self._func_pins.items():
            self._func_values[name], self._func_times[name], pressed = \
                self._scan_pin(pin, self._func_values[name], self._func_times[name], now)
            if pressed:
                events['funcs'].append(name)

        return events
