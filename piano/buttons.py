"""
buttons.py - 9 键数字钢琴按键扫描模块（优化版）

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- 音阶键：GPIO23/22/21/19/18/14/12 → do/re/mi/fa/sol/la/si
- 功能键：GPIO34(八度+), GPIO35(八度-)
- 电平特性：内部上拉，按下 = 低电平(0)

去抖策略：
- 每次 scan 同时读取所有引脚，不 sleep。
- 记录每个引脚的原始状态和稳定状态，以及状态变化时刻。
- 仅当原始状态持续稳定超过 debounce_ms 后，才更新稳定状态。
- 只在稳定状态出现按下沿（1→0）时报告事件。
"""

from machine import Pin
import time

# 音阶键 GPIO，顺序对应 do/re/mi/fa/sol/la/si
NOTE_GPIOS = (23, 22, 21, 19, 18, 14, 12)
NOTE_NAMES = ('do', 're', 'mi', 'fa', 'sol', 'la', 'si')

# 功能键 GPIO
FUNC_GPIOS = {
    'octave_up': 34,
    'octave_down': 35,
}

# 默认去抖时间（毫秒）
DEFAULT_DEBOUNCE_MS = 20


class ButtonMatrix:
    """按键矩阵扫描类，支持音阶键和功能键。"""

    def __init__(self, debounce_ms=DEFAULT_DEBOUNCE_MS):
        self.debounce_ms = debounce_ms
        self._note_pins = [Pin(gpio, Pin.IN, Pin.PULL_UP) for gpio in NOTE_GPIOS]
        self._func_pins = {
            name: Pin(gpio, Pin.IN, Pin.PULL_UP)
            for name, gpio in FUNC_GPIOS.items()
        }

        # 稳定状态：1=释放，0=按下
        self._note_stable = [1] * len(NOTE_GPIOS)
        self._func_stable = {name: 1 for name in FUNC_GPIOS}
        # 上一次读取的原始状态
        self._note_raw = [1] * len(NOTE_GPIOS)
        self._func_raw = {name: 1 for name in FUNC_GPIOS}
        # 状态变化时刻（毫秒）
        self._note_changed_at = [0] * len(NOTE_GPIOS)
        self._func_changed_at = {name: 0 for name in FUNC_GPIOS}

    def _read_all(self):
        """一次性读取所有按键原始状态。"""
        note_values = [pin.value() for pin in self._note_pins]
        func_values = {name: pin.value() for name, pin in self._func_pins.items()}
        return note_values, func_values

    def _update_note_states(self, values, now):
        """更新音阶键稳定状态，返回按下沿索引列表。"""
        events = []
        for idx, val in enumerate(values):
            if val != self._note_raw[idx]:
                self._note_raw[idx] = val
                self._note_changed_at[idx] = now

            if val != self._note_stable[idx]:
                if time.ticks_diff(now, self._note_changed_at[idx]) >= self.debounce_ms:
                    old_stable = self._note_stable[idx]
                    self._note_stable[idx] = val
                    if old_stable == 1 and val == 0:
                        events.append(idx)
        return events

    def _update_func_states(self, values, now):
        """更新功能键稳定状态，返回按下沿名称列表。"""
        events = []
        for name, val in values.items():
            if val != self._func_raw[name]:
                self._func_raw[name] = val
                self._func_changed_at[name] = now

            if val != self._func_stable[name]:
                if time.ticks_diff(now, self._func_changed_at[name]) >= self.debounce_ms:
                    old_stable = self._func_stable[name]
                    self._func_stable[name] = val
                    if old_stable == 1 and val == 0:
                        events.append(name)
        return events

    def scan_all(self):
        """
        扫描全部按键。
        返回：{'notes': [idx, ...], 'funcs': [name, ...]}
        只返回本次 newly pressed（按下沿）的键。
        """
        now = time.ticks_ms()
        note_values, func_values = self._read_all()

        return {
            'notes': self._update_note_states(note_values, now),
            'funcs': self._update_func_states(func_values, now),
        }

    def get_pressed_keys(self):
        """
        返回当前所有被按下的键名列表。
        包含音符名(do/re/...)和功能键名(octave_up/octave_down)。
        """
        pressed = []
        for idx, pin in enumerate(self._note_pins):
            if pin.value() == 0:
                pressed.append(NOTE_NAMES[idx])
        for name, pin in self._func_pins.items():
            if pin.value() == 0:
                pressed.append(name)
        return pressed

    def get_octave_shift(self):
        """
        返回八度偏移：+1(八度+按下), -1(八度-按下), 0(均未按)。
        若同时按下，按相反方向抵消。
        """
        up = self._func_pins['octave_up'].value() == 0
        down = self._func_pins['octave_down'].value() == 0
        return (1 if up else 0) - (1 if down else 0)
