"""
piano.py - 数字钢琴主控制逻辑（W3 硬件直驱 LED 版）

硬件上下文：
- 开发板：ESP32-D0WD-V3 + MicroPython v1.23.0
- 音阶键：GPIO23/22/21/19/18/14/12 → do/re/mi/fa/sol/la/si
- 功能键：GPIO34(八度+), GPIO35(八度-)
- 控制键：GPIO5(短按=开始/停止录制，长按=播放)
- LED 直驱接线：3.3V → LED → 330Ω → 按键 → GND
  GPIO 只做输入检测，不控制 LED
- I2S 功放：MAX98357A, BCLK=GPIO16, LRC=GPIO17, DIN=GPIO25

核心设计：
- 边沿检测：按下瞬间发声，释放瞬间静音。
- LED 由按键回路硬件直驱，声光零延迟。
- 多键支持：同时按住多个键，喇叭播放最后按下的音。
- 录制/播放：GPIO5 短按切换录制，长按播放最近录制的内容。
"""

import time

from machine import Pin
from buttons import ButtonController
from i2s_audio import I2SAudio

# 音符顺序
NOTE_NAMES = ('do', 're', 'mi', 'fa', 'sol', 'la', 'si')

# 运行状态
STATE_IDLE = 0
STATE_RECORDING = 1
STATE_PLAYING = 2

# 录制/播放按键参数
RECORD_LONG_PRESS_MS = 800  # 长按阈值

# 板载 LED（低电平点亮），用于指示八度模式
LED_UP_GPIO = 32    # 绿灯：高八度
LED_DOWN_GPIO = 33  # 红灯：低八度

# 音符到基础频率的映射（中音 C4 开始）
NOTE_FREQS = {
    'do': 262,
    're': 294,
    'mi': 330,
    'fa': 349,
    'sol': 392,
    'la': 440,
    'si': 494,
}


class Piano:
    """数字钢琴：硬件直驱 LED，软件只控制声音。"""

    def __init__(self):
        self.buttons = ButtonController()
        self.audio = I2SAudio()
        self.octave_shift = 0

        # 上一次的按键状态（用于边沿检测）
        self.prev = {name: False for name in self.buttons.key_names}

        # 当前按下的音符列表（有序，支持多键，最后按下优先）
        self.active = []

        # 板载 LED 指示八度模式（1=灭，0=亮）
        self._led_up = Pin(LED_UP_GPIO, Pin.OUT, value=1)
        self._led_down = Pin(LED_DOWN_GPIO, Pin.OUT, value=1)

        # 录制/播放状态
        self._state = STATE_IDLE
        self._recording = []       # 录制事件列表
        self._record_start_ms = 0
        self._record_press_start = 0
        self._record_long_triggered = False

        # 播放状态
        self._playback_events = []
        self._playback_index = 0
        self._playback_start_ms = 0

    def _freq_with_octave(self, base_freq):
        """应用八度偏移。"""
        if self.octave_shift == 1:
            return base_freq * 2
        elif self.octave_shift == -1:
            return base_freq // 2
        return base_freq

    def _play_last_note(self):
        """播放当前按下的最后一个音符；无按键则静音。"""
        if self.active:
            last = self.active[-1]
            freq = self._freq_with_octave(NOTE_FREQS[last])
            self.audio.play_tone(freq)
        else:
            self.audio.stop()

    def tick(self):
        """
        每帧调用（建议 5ms 间隔）。
        - 检测八度键并更新 octave_shift
        - 边沿检测处理 7 个音调键
        """
        # ─── 八度检测（按一下切换，永久生效） ───
        up = self.buttons.is_pressed('octave_up')
        down = self.buttons.is_pressed('octave_down')

        if up and not self.prev['octave_up']:
            # 升八度键按下沿：在 0 和 +1 之间切换
            self.octave_shift = 1 if self.octave_shift != 1 else 0
        if down and not self.prev['octave_down']:
            # 降八度键按下沿：在 0 和 -1 之间切换
            self.octave_shift = -1 if self.octave_shift != -1 else 0

        self.prev['octave_up'] = up
        self.prev['octave_down'] = down

        # ─── GPIO5 录制/播放键（短按=开始/停止录制，长按=播放） ───
        self._handle_record_play_key()

        # 更新 LED 指示（八度模式 / 录制 / 播放）
        self._update_leds()

        # ─── 7 个音调键 ───
        for note in NOTE_NAMES:
            curr = self.buttons.is_pressed(note)
            prev = self.prev[note]

            if curr and not prev:
                # 上升沿（按下）：加入 active 并立即播放
                if note not in self.active:
                    self.active.append(note)
                    self._record_event('note_on', note)
                self._play_last_note()

            elif not curr and prev:
                # 下降沿（释放）：从 active 移除
                if note in self.active:
                    self.active.remove(note)
                    self._record_event('note_off', note)
                self._play_last_note()

            self.prev[note] = curr

        # 持续补充 I2S 缓冲，防止后台线程断流
        if self.active:
            self._play_last_note()

        # ─── 播放进度更新 ───
        if self._state == STATE_PLAYING:
            self._update_playback()

    def _handle_record_play_key(self):
        """处理 GPIO5 录制/播放键：短按切换录制，长按播放。"""
        now = time.ticks_ms()
        curr = self.buttons.is_pressed('record_play')
        prev = self.prev.get('record_play', False)

        if curr and not prev:
            # 按下沿：记录按下时间，复位长按标志
            self._record_press_start = now
            self._record_long_triggered = False
        elif curr and prev:
            # 持续按住：达到长按阈值时触发播放
            if (not self._record_long_triggered and
                    time.ticks_diff(now, self._record_press_start) >= RECORD_LONG_PRESS_MS):
                self._record_long_triggered = True
                self._start_playback()
        elif not curr and prev:
            # 释放沿：如果不是长按，则短按切换录制
            if not self._record_long_triggered:
                self._toggle_recording()

        self.prev['record_play'] = curr

    def _toggle_recording(self):
        """短按：在空闲和录制状态之间切换。"""
        if self._state == STATE_RECORDING:
            self._stop_recording()
        elif self._state == STATE_IDLE:
            self._start_recording()
        # 播放中短按无效

    def _start_recording(self):
        """开始录制。"""
        self._state = STATE_RECORDING
        self._recording = []
        self._record_start_ms = time.ticks_ms()
        self.audio.stop()
        self.active = []
        print("开始录制...")

    def _stop_recording(self):
        """停止录制。"""
        self._state = STATE_IDLE
        # 自动补全所有仍按下的音符的释放事件
        now = time.ticks_ms()
        for note in list(self.active):
            rel_time = time.ticks_diff(now, self._record_start_ms)
            self._recording.append({
                'type': 'note_off',
                'note': note,
                'octave': self.octave_shift,
                'time': rel_time,
            })
        self.active = []
        self.audio.stop()
        print("停止录制，共记录 {} 个事件".format(len(self._recording)))

    def _record_event(self, event_type, note):
        """录制时记录一个音符事件。"""
        if self._state != STATE_RECORDING:
            return
        now = time.ticks_ms()
        rel_time = time.ticks_diff(now, self._record_start_ms)
        self._recording.append({
            'type': event_type,
            'note': note,
            'octave': self.octave_shift,
            'time': rel_time,
        })

    def _start_playback(self):
        """开始播放录制内容。"""
        if not self._recording:
            print("没有录制内容，无法播放")
            return
        if self._state == STATE_PLAYING:
            return
        self._state = STATE_PLAYING
        self._playback_events = list(self._recording)
        self._playback_index = 0
        self._playback_start_ms = time.ticks_ms()
        self.active = []
        self.audio.stop()
        print("开始播放")

    def _update_playback(self):
        """按时间触发录制的事件。"""
        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self._playback_start_ms)

        while self._playback_index < len(self._playback_events):
            ev = self._playback_events[self._playback_index]
            if ev['time'] <= elapsed:
                self._playback_index += 1
                if ev['type'] == 'note_on':
                    self.octave_shift = ev.get('octave', 0)
                    if ev['note'] not in self.active:
                        self.active.append(ev['note'])
                    self._play_last_note()
                elif ev['type'] == 'note_off':
                    if ev['note'] in self.active:
                        self.active.remove(ev['note'])
                    self._play_last_note()
            else:
                break

        if self._playback_index >= len(self._playback_events):
            self._stop_playback()

    def _stop_playback(self):
        """停止播放。"""
        self._state = STATE_IDLE
        self.active = []
        self.audio.stop()
        print("播放结束")

    def _update_leds(self):
        """根据当前状态更新板载 LED。"""
        if self._state == STATE_RECORDING:
            # 录制中：绿灯亮
            self._led_up.value(0)
            self._led_down.value(1)
        elif self._state == STATE_PLAYING:
            # 播放中：红灯亮
            self._led_up.value(1)
            self._led_down.value(0)
        else:
            # 空闲：指示八度模式
            self._led_up.value(0 if self.octave_shift == 1 else 1)
            self._led_down.value(0 if self.octave_shift == -1 else 1)

    def close(self):
        """停止发声。"""
        self.audio.stop()

    def run(self):
        """持续运行钢琴主循环。"""
        print("MCPiano 启动，按 Ctrl+C 停止")
        try:
            while True:
                self.tick()
                time.sleep_ms(5)
        except KeyboardInterrupt:
            self.close()
            print("\nMCPiano 已停止")
