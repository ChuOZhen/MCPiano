# ─────────────────────────────────────────────────────
# AutoContextExtension: MCPiano
# Agent: KimiCode
# Type: Embedded AI-Native Development
# Template: v1.0
# ─────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════
# 1. PROJECT IDENTITY
# ═══════════════════════════════════════════════════

project:
  name: MCPiano
  repository: https://github.com/ChuOZhen/MCPiano.git
  agent: KimiCode
  paradigm: AI-Native Embedded Development
  duration: 2026/07/06 – 2026/08/09
  platform: ESP32-D0WD-V3
  firmware: MicroPython
  toolchain_lang: Python 3.10+
  protocol: Model Context Protocol (MCP)

# ═══════════════════════════════════════════════════
# 2. DUAL-TASK ARCHITECTURE
# ═══════════════════════════════════════════════════

┌─────────────────────────────────────────────────┐
│              MCPiano Project                     │
│  ┌──────────────┐      ┌──────────────┐         │
│  │   T1: Piano  │      │  T2: Tool    │         │
│  │   Firmware   │◄────►│  Chain MCP   │         │
│  │  (Embedded)  │      │  (Host)      │         │
│  └──────────────┘      └──────────────┘         │
│        ▲                      ▲                  │
│        │      Validates       │                  │
│        └──────────────────────┘                  │
└─────────────────────────────────────────────────┘

# ═══════════════════════════════════════════════════
# 3. HARDWARE CONTEXT (Immutable)
# ═══════════════════════════════════════════════════

## 3.1 GPIO Mapping

| Pin | GPIO | Direction | Pull | Active | Usage | Required |
|-----|------|-----------|------|--------|-------|----------|
| KEY1 | 34 | IN | UP | LOW | Piano Key 1 | YES |
| KEY2 | 35 | IN | UP | LOW | Piano Key 2 | YES |
| LED2 | 32 | OUT | — | LOW | Green LED | YES |
| LED3 | 33 | OUT | — | LOW | Red LED | YES |
| BUZ1 | 25 | PWM | — | HIGH | Buzzer (NPN) | YES |
| BOOT | 0 | IN | — | — | Boot mode | — |
| SDA | 16 | I2C | — | — | MPU6050 (opt) | NO |
| SCL | 17 | I2C | — | — | MPU6050 (opt) | NO |

## 3.2 Note Frequency Table

| Note | Freq (Hz) | Note | Freq (Hz) |
|------|-----------|------|-----------|
| C4 (do) | 261.63 | G4 (sol) | 392.00 |
| D4 (re) | 293.66 | A4 (la) | 440.00 |
| E4 (mi) | 329.63 | B4 (si) | 493.88 |
| F4 (fa) | 349.23 | C5 | 523.25 |

## 3.3 Hardware Constraints

- [FIRM] Buzzer: GPIO25, PWM, HIGH-active, NPN (MMSS8050) driver
- [FIRM] LED: LOW-active (0=on, 1=off)
- [FIRM] Keys: Internal pull-up, pressed=LOW
- [FIRM] UART: CP2102N, baud 115200 default
- [FIRM] Flash: 32Mbit SPI Flash (ZB25VQ32)

# ═══════════════════════════════════════════════════
# 4. FILE MAP
# ═══════════════════════════════════════════════════

repository/
├── README.md                    # Project info, members, nav
├── piano/                       # MicroPython firmware
│   ├── main.py                  # Entry: init + event loop
│   ├── buttons.py               # GPIO34/35 driver, debounce
│   ├── buzzer.py                # GPIO25 PWM, note table
│   ├── leds.py                  # GPIO32/33, LOW-active
│   └── piano.py                 # State machine, app logic
├── toolchain/                   # MCP toolchain (Python)
│   ├── mcp_server.py            # MCP server entry
│   ├── tools/
│   │   ├── file_transfer.py     # Raw REPL upload/download
│   │   ├── serial_monitor.py   # Async serial listener
│   │   ├── executor.py          # Remote exec/stop
│   │   └── error_handler.py     # Traceback parser
│   └── README.md                # Toolchain guide
├── hardware/
│   ├── schematic.pdf            # Authority: GPIO mapping
│   ├── pcb.pdf                  # Physical layout
│   └── bom_analysis.md          # Resource allocation
├── tests/                       # Hardware validation
│   ├── test_button.py
│   ├── test_buzzer.py
│   ├── test_led.py
│   └── test_mpu6050.py
├── docs/                        # Architecture docs
├── images/                      # Screenshots, diagrams
└── report/                      # Final report source

# ═══════════════════════════════════════════════════
# 5. MCP TOOL DEFINITIONS
# ═══════════════════════════════════════════════════

## 5.1 Required Tools (6)

tool: esp32_upload
  desc: Push local MicroPython file to ESP32
  params: [local_path: str, remote_path: str]
  returns: {success: bool, message: str}
  protocol: raw_repl

tool: esp32_execute
  desc: Remote start/stop user program
  params: [entry_file: str, action: "start"|"stop"]
  returns: {success: bool}

tool: esp32_reset
  desc: Soft or hard reset ESP32
  params: [mode: "soft"|"hard"]
  returns: {success: bool}
  note: soft=machine.reset(), hard=DTR/RTS

tool: esp32_serial
  desc: Real-time serial monitor
  params: [action: "start"|"stop"|"read", duration: int?]
  returns: {lines: list[str]}
  note: async thread, ring buffer 1000 lines

tool: esp32_logs
  desc: Retrieve execution logs
  params: [lines: int=50, filter: str?]
  returns: {logs: list[str]}

tool: esp32_error
  desc: Auto-detect MicroPython runtime errors
  params: [auto_parse: bool=true]
  returns: {error: {file, line, type, message}?}
  regex: Traceback \(most recent call last\):.*\n  File "(.+)", line (\d+).*\n    .+\n(\w+): (.+)

## 5.2 Optional Tools (≥1)

tool: esp32_filesystem
  desc: Remote ls/rm/cat
  priority: HIGH

tool: esp32_regression
  desc: Auto test: upload→exec→assert output
  priority: HIGH

tool: esp32_gpio_query
  desc: Online GPIO status query
  priority: MEDIUM

tool: esp32_flash
  desc: Auto flash MicroPython firmware
  priority: MEDIUM

tool: esp32_hwinfo
  desc: Auto collect MAC/Flash/CPU info
  priority: LOW

tool: esp32_profile
  desc: Memory/CPU profiling
  priority: LOW

# ═══════════════════════════════════════════════════
# 6. COMMUNICATION STACK
# ═══════════════════════════════════════════════════

┌─────────────────────────────────────────────────┐
│  Host (Python 3.10+)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ MCP      │──│ pyserial │──│ CP2102N  │    │
│  │ Server   │  │          │  │ USB-UART │    │
│  └──────────┘  └──────────┘  └──────────┘    │
└──────────────────────┬──────────────────────────┘
                       │ Serial 115200
                       ▼
┌─────────────────────────────────────────────────┐
│  ESP32-D0WD-V3 (MicroPython)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ REPL     │──│ Raw REPL │──│ FS/Exec  │       │
│  │          │  │ Protocol │  │ Engine   │       │
│  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────┘

# ═══════════════════════════════════════════════════
# 7. CODE CONVENTIONS
# ═══════════════════════════════════════════════════

rules:
  - All GPIO ops MUST be encapsulated in driver modules
  - No direct GPIO access in main.py
  - Single file ≤ 200 lines
  - All functions MUST have docstrings with hardware context
  - Error handling MUST include peripheral/GPIO context
  - All code MUST be hardware-validated before commit
  - Use machine.PWM for buzzer, no third-party libs
  - Use asyncio or threading for serial monitor

# ═══════════════════════════════════════════════════
# 8. WEEKLY SPRINTS
# ═══════════════════════════════════════════════════

## W1 (7/6–7/12): Hardware Onboarding
- Parse schematic → bom_analysis.md
- Flash MicroPython firmware
- Per-test: button, LED, buzzer
- Read mini-claude-code → notes
- Select: MCP server approach
- Deliver: Bilibili W1 video

## W2 (7/13–7/19): Piano Core + Architecture
- Piano v1: buttons→buzzer→leds→piano→main
- Toolchain architecture doc
- Init mcp_server.py skeleton
- Deliver: Bilibili W2 video

## W3 (7/20–7/26): Toolchain Dev
- Impl: file_transfer → serial_monitor → executor → error_handler → reset → logs
- Register all 6 tools to MCP server
- CLI self-test each tool
- Deliver: Bilibili W3 video

## W4 (7/27–8/2): Integration & Closed Loop
- Integrate MCP server with KimiCode
- Design bug scenario for AI self-healing
- Execute ≥1 full AI iteration loop
- Record: AI dialog → code fix → upload → run → verify
- Save logs as evidence
- Deliver: Bilibili W4 video (CRITICAL)

## W5 (8/3–8/9): Polish & Deliver
- Extension: octave / record / MPU6050
- Final report: 15–20 pages PDF
- GitHub cleanup: README, comments, history
- Deliver: Bilibili W5 video + Report to 349744305@qq.com

# ═══════════════════════════════════════════════════
# 9. RED LINES (Never Violate)
# ═══════════════════════════════════════════════════

- [CRITICAL] All code must be hardware-validated before submission
- [CRITICAL] Toolchain MUST demonstrate ≥1 complete AI self-healing loop
- [CRITICAL] Fake closed-loop demo = academic dishonesty
- [CRITICAL] Engineer must understand every line of submitted code
- [CRITICAL] Toolchain architecture must be engineer-designed, not AI-delegated
- [CRITICAL] GPIO numbers must be verified against schematic, never assumed

# ═══════════════════════════════════════════════════
# 10. AI PROMPT TEMPLATES
# ═══════════════════════════════════════════════════

## MicroPython Driver Request

[Context]
Board: ESP32-D0WD-V3, MicroPython firmware
Peripheral: <device> on GPIO< n >, <driver_type>, <active_level>

[Task]
Write a MicroPython module that:
1. <requirement_1>
2. <requirement_2>

[Interface]
- <func_signature>

[Constraints]
- Use machine.<module>, no third-party libs
- Include hardware test snippet
- Include error handling

## Toolchain Tool Request

[Context]
Stack: Python 3.10+, MCP SDK, pyserial
Target: ESP32 via CP2102N USB-UART @115200
Protocol: MicroPython raw REPL

[Task]
Implement MCP tool <tool_name> that:
1. <functionality>

[Interface]
- Input: <params>
- Output: <returns>

[Constraints]
- Handle serial timeout and validation
- Error messages include hardware context
- Include pytest test case with mock serial

# ═══════════════════════════════════════════════════
# 11. REFERENCES
# ═══════════════════════════════════════════════════

- mini-claude-code: https://github.com/ShareAI-Lab/mini-claude-code
- MCP Spec: https://modelcontextprotocol.io
- MicroPython REPL: https://docs.micropython.org/en/latest/reference/repl.html
- ampy: https://github.com/scientifichackers/ampy
- Teacher: 349744305@qq.com
- Agent Context: ./kimi.md (this file)
- Personal Tracker: ./mine.md

# ═══════════════════════════════════════════════════
# AutoContextExtension End
# ═══════════════════════════════════════════════════
