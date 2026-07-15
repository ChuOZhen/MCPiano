"""
piano.py - 9 键数字钢琴应用逻辑

硬件上下文：
- 7 个音阶键：GPIO23/22/21/19/18/14/12 → do/re/mi/fa/sol/la/si
- 2 个功能键：GPIO34(八度+), GPIO35(八度-)
- 音频输出：通过 i2s_audio.I2SAudio（GPIO16/17/25 I2S）

本模块只管理音阶/八度状态和按键响应，不直接操作 GPIO。
"""

OCTAVES = {
    0: {'name': 'C3', 'base': 131},  # 低八度
    1: {'name': 'C4', 'base': 262},  # 中音（默认）
    2: {'name': 'C5', 'base': 523},  # 高八度
}

NOTES = ['do', 're', 'mi', 'fa', 'sol', 'la', 'si']
NOTE_RATIOS = [1.0, 1.122, 1.26, 1.335, 1.498, 1.682, 1.888]


class Piano:
    """9 键数字钢琴状态机。"""

    def __init__(self, audio, button_matrix, enable_led=False):
        """
        初始化钢琴应用。

        Args:
            audio: I2SAudio 实例，负责音频输出。
            button_matrix: ButtonMatrix 实例，负责按键扫描。
            enable_led: 是否启用 LED（本次无 330Ω 电阻，默认 False）。
        """
        self.audio = audio
        self.buttons = button_matrix
        self.enable_led = enable_led
        self.current_octave = 1  # 默认中音 C4

    def _freq_for(self, note_idx):
        """
        根据当前八度计算音符频率。

        Args:
            note_idx: 0~6 对应 do~si。

        Returns:
            int: 频率（Hz），取整。
        """
        base = OCTAVES[self.current_octave]['base']
        return int(base * NOTE_RATIOS[note_idx])

    def play_note(self, note_idx):
        """
        播放指定索引的音符。

        Args:
            note_idx: 0~6 对应 do~si。
        """
        if not 0 <= note_idx <= 6:
            raise ValueError(f"note_idx 必须在 0~6 之间：{note_idx}")

        freq = self._freq_for(note_idx)
        note_name = NOTES[note_idx]
        octave_name = OCTAVES[self.current_octave]['name']
        print(f"🎵 播放 {note_name} ({freq}Hz, {octave_name})")
        self.audio.play_tone(freq, 300)

    def _shift_octave(self, direction):
        """
        切换八度。

        Args:
            direction: +1 表示升八度，-1 表示降八度。
        """
        new_octave = self.current_octave + direction
        if 0 <= new_octave <= 2:
            self.current_octave = new_octave
            octave_name = OCTAVES[self.current_octave]['name']
            print(f"🎹 切换到 {octave_name} 八度")
        else:
            print("⚠️ 已到达最高/最低八度")

    def handle_events(self, events):
        """
        处理按键事件。

        Args:
            events: dict，格式 {'notes': [idx, ...], 'funcs': [name, ...]}
        """
        for note_idx in events.get('notes', []):
            try:
                self.play_note(note_idx)
            except Exception as e:
                print(f"❌ 播放音符失败 idx={note_idx}：{e}")

        for func in events.get('funcs', []):
            if func == 'octave_up':
                self._shift_octave(+1)
            elif func == 'octave_down':
                self._shift_octave(-1)
            else:
                print(f"⚠️ 未知功能键：{func}")

    def tick(self):
        """每帧调用：扫描按键并处理事件。"""
        events = self.buttons.scan_all()
        if events['notes'] or events['funcs']:
            self.handle_events(events)
