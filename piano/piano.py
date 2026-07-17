"""
piano.py - 数字钢琴主控制逻辑

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- 音阶键：GPIO23/22/21/19/18/14/12 → do/re/mi/fa/sol/la/si
- 功能键：GPIO34(八度+), GPIO35(八度-)
- LED：GPIO32(绿), GPIO33(红)，低电平点亮
"""

import time
from machine import Pin

from i2s_audio import I2SAudio
from buttons import ButtonMatrix, NOTE_NAMES, NOTE_GPIOS

# 音符顺序（供外部枚举，保证 MicroPython 迭代顺序）
NOTES = ('do', 're', 'mi', 'fa', 'sol', 'la', 'si')

# 音符到基础频率的映射（中音 C4 开始）
_FREQS = {
    'do': 262,
    're': 294,
    'mi': 330,
    'fa': 349,
    'sol': 392,
    'la': 440,
    'si': 494,
}

# 支持的八度偏移范围
OCTAVES = (-1, 0, 1)

# LED GPIO
GREEN_LED_GPIO = 32
RED_LED_GPIO = 33

# 默认音符持续时间（毫秒）
NOTE_DURATION_MS = 300


class Piano:
    """数字钢琴状态机：按键扫描 → 八度计算 → 发声 → LED 反馈。"""

    def __init__(self, audio, buttons, enable_led=True):
        self.audio = audio
        self.buttons = buttons
        self.enable_led = enable_led
        self.octave = 0

        if self.enable_led:
            self._green = Pin(GREEN_LED_GPIO, Pin.OUT, value=1)
            self._red = Pin(RED_LED_GPIO, Pin.OUT, value=1)
        else:
            self._green = None
            self._red = None

    def _led_note_on(self):
        """弹琴键时点亮绿灯，熄灭红灯。"""
        if self._green is not None:
            self._green.value(0)
        if self._red is not None:
            self._red.value(1)

    def _led_octave_on(self):
        """调八度时点亮红灯，熄灭绿灯。"""
        if self._green is not None:
            self._green.value(1)
        if self._red is not None:
            self._red.value(0)

    def _led_off(self):
        """熄灭两个 LED。"""
        if self._green is not None:
            self._green.value(1)
        if self._red is not None:
            self._red.value(1)

    def _freq_for(self, idx):
        """根据音符索引和当前八度计算实际频率。"""
        name = NOTE_NAMES[idx]
        base = _FREQS[name]
        return int(base * (2 ** self.octave))

    def play_note(self, idx, duration_ms=NOTE_DURATION_MS):
        """播放指定索引的音符。"""
        freq = self._freq_for(idx)
        self.audio.play_tone(freq, duration_ms)
        self._led_note_on()
        return freq

    def handle_events(self, events):
        """处理按键事件：播放音符或调整八度。"""
        for idx in events.get('notes', []):
            self.play_note(idx)

        for func in events.get('funcs', []):
            if func == 'octave_up':
                self.octave = min(self.octave + 1, max(OCTAVES))
            elif func == 'octave_down':
                self.octave = max(self.octave - 1, min(OCTAVES))
            self._led_octave_on()

    def tick(self):
        """主循环 tick：扫描按键并处理事件，LED 跟随按键状态。"""
        events = self.buttons.scan_all()
        self.handle_events(events)

        pressed = set(self.buttons.get_pressed_keys())
        has_note = any(name in pressed for name in NOTE_NAMES)
        has_octave = 'octave_up' in pressed or 'octave_down' in pressed

        if has_note:
            self._led_note_on()
        elif has_octave:
            self._led_octave_on()
        else:
            self._led_off()

    def reset_octave(self):
        """将八度恢复到默认值。"""
        self.octave = 0

    def run(self):
        """持续运行钢琴主循环。"""
        print("MCPiano 启动，按 Ctrl+C 停止")
        try:
            while True:
                self.tick()
                time.sleep_ms(10)
        except KeyboardInterrupt:
            self.stop()
            print("\nMCPiano 已停止")

    def stop(self):
        """停止发声并熄灭 LED。"""
        self.audio.stop()
        self._led_off()
