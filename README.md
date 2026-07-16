# MCPiano — AI 原生嵌入式数字钢琴 & 开发工具链

---

## 项目概述

 本项目包含 **两个相互关联的工程任务**：

### 任务一：数字钢琴

 利用 ESP32 开发板实现一台功能完整的 9 键数字钢琴：

- **按键输入**：9 个面包板按键
  - GPIO23/22/21/19/18/14/12 → do/re/mi/fa/sol/la/si（7 音阶）
  - GPIO34 → 八度+
  - GPIO35 → 八度-
- **音符生成**：通过 MAX98357A I2S 功放模块 + 喇叭，输出 16-bit 正弦波 PCM 音频
- **视觉反馈**：预留 LED 接口，本次因无 330Ω 限流电阻暂不启用；OLED 显示当前音符（可选，GPIO2/4 I2C）
- **系统稳定性**：上电自动进入工作状态，持续稳定响应

### 任务二：AI 原生开发工具链

 设计并实现一套工具链，使 AI 编程助手能直接与 ESP32 开发板交互：

| 序号 | 能力         | 描述                                 |
| ---- | ------------ | ------------------------------------ |
| 1    | 文件传输     | AI 将 MicroPython 源文件推送到 ESP32 |
| 2    | 程序执行     | AI 远程触发用户程序的运行和停止      |
| 3    | 微控制器复位 | AI 通过软件命令重启 ESP32            |
| 4    | 串口监控     | AI 实时捕获并读取 ESP32 的串口输出   |
| 5    | 运行日志检索 | AI 收集程序执行日志                  |
| 6    | 错误报告     | AI 自动检测 MicroPython 运行时异常   |

 以数字钢琴为验证基准，演示 AI 通过工具链驱动嵌入式开发的 **完整闭环**（AI 发现问题 → 修改代码 → 自动部署 → 验证通过）。

---

## 目录结构

```
~/MCPpiano/
├── README.md
├── .gitignore
├── piano/                       # 数字钢琴固件（MicroPython）
│   ├── i2s_audio.py             # MAX98357A I2S 功放驱动（16-bit 正弦波）
│   ├── buttons.py               # 9 键扫描（7 音阶 + 2 功能键）
│   ├── piano.py                 # 钢琴状态机（音阶/八度/响应）
│   └── main.py                  # 上电自动运行入口
├── toolchain/                   # AI 原生工具链（Python）
│   └── tools/
├── hardware/                    # 硬件工程文档
│   ├── schematic.pdf            # 原理图
│   ├── pcb.pdf                  # PCB 版图
│   ├── MCPiano_硬件资源分析.xlsx
│   └── bom_analysis.md          # BOM 与硬件资源分析
├── tests/                       # 外设测试脚本
│   ├── test_button.py           # 原 2 键按键测试
│   ├── test_buzzer.py           # 已废弃：原 GPIO25 PWM 蜂鸣器测试
│   ├── test_led.py              # LED 指示灯测试
│   ├── test_max98357a.py        # MAX98357A I2S 功放独立测试
│   ├── test_buttons_9key.py     # 9 键手动按压检测
│   ├── test_piano_v1.py         # 9 键钢琴系统综合测试
│   └── test_ssd1306.py          # SSD1306 OLED I2C 显示测试
├── docs/                        # 技术文档
│   ├── mini_claude_code_notes.md
│   ├── toolchain_proposal.md
│   └── 最新25级实验班暑假大作业要求.pdf
├── images/                      # 演示截图、视频封面
└── report/                      # 最终技术报告
```

---

## 开发环境

| 组件       | 要求                           |
| ---------- | ------------------------------ |
| 开发语言   | MicroPython + Python（工具链） |
| 目标硬件   | ESP32-D0WD-V3 开发板           |
| 代码编辑器 | 不限（推荐 VS Code）           |
| 烧录工具   | esptool.py + MicroPython 固件  |
| 串口工具   | 调试输出和 REPL 交互           |
| 版本控制   | Git + GitHub（公共仓库）       |

---

## 快速开始

### 1. 进入虚拟环境

```bash
cd ~/MCPpiano
source .venv/bin/activate
```

### 2. 运行 I2S 功放测试

```bash
mpremote connect /dev/ttyACM0 run tests/test_max98357a.py
```

> 听到清晰正弦波七音阶即表示音频模块工作正常。

### 3. 运行 OLED 显示测试

```bash
mpremote connect /dev/ttyACM0 run tests/test_ssd1306.py
```

> OLED 依次显示 "MCPiano"、七音阶名、动态播放信息。

### 4. 运行钢琴系统综合测试

```bash
mpremote connect /dev/ttyACM0 cp piano/i2s_audio.py :
mpremote connect /dev/ttyACM0 cp piano/buttons.py :
mpremote connect /dev/ttyACM0 cp piano/piano.py :
mpremote connect /dev/ttyACM0 run tests/test_piano_v1.py
```

> 按下按键能听到对应音阶，八度+/- 能切换音高。

### 5. 直接运行钢琴主程序

```bash
mpremote connect /dev/ttyACM0 cp piano/i2s_audio.py :
mpremote connect /dev/ttyACM0 cp piano/buttons.py :
mpremote connect /dev/ttyACM0 cp piano/piano.py :
mpremote connect /dev/ttyACM0 run piano/main.py
```

### 6. 运行其他外设测试

```bash
mpremote connect /dev/ttyACM0 run tests/test_button.py
mpremote connect /dev/ttyACM0 run tests/test_led.py
```

---

## 硬件连接

### MAX98357A I2S 功放接线

| 信号 | ESP32 GPIO | MAX98357A 引脚 | 说明 |
|:-----|:----------:|:--------------|:-----|
| BCLK | **GPIO16** | BCLK | I2S 位时钟 |
| LRCK | **GPIO17** | LRCK | I2S 帧时钟（WS） |
| DIN  | **GPIO25** | DIN  | I2S 数据输入 |
| 5V   | 5V 排针    | VIN  | 功放供电（必须 5V，不能接 3.3V） |
| GND  | GND 排针   | GND  | 与 ESP32 共地 |
| GAIN | **5V 排针** | GAIN | **本模块接 VIN = 正常增益；接 GND 会变成高增益，导致小音量削顶** |
| SD_MODE | 5V 排针 | SD_MODE | **必须接 VIN，不能悬空；接 GND 会关闭功放** |

> ⚠️ **注意模块差异**：市面上 MAX98357A 模块的 GAIN 逻辑不统一。本项目的模块**GND=高增益、VIN=正常增益**，因此 GAIN 接 VIN。如果你的模块相反，表现为音量数字越大声音越小，请把 GAIN 改接 GND。
>
> ⚠️ **SD_MODE 悬空会导致功放状态不稳定**，表现为大音量反而变小、间歇失声或底噪异常。

### SSD1306 OLED 接线

| SSD1306 OLED | VCC | GND | SCL | SDA |
|:-------------|:----|:----|:----|:----|
| 接 ESP32 | 5V | GND | GPIO2 | GPIO4 |

> ⚠️ **GPIO2 启动模式注意**：GPIO2 在 ESP32 启动时连接板载蓝色 LED，低电平可能影响下载模式。如果下载固件失败，下载时请断开 GPIO2 的 SCL 线。
>
> 默认 I2C 地址为 `0x3C`；若花屏或不显示，可尝试 `addr=0x3D`。

### 其他外设（保留）

| 外设 | GPIO | 方向 | 电平特性 |
|:-----|:----:|:----:|:---------|
| KEY1 | 34 | 输入 | 内部上拉，按下 = 低电平 |
| KEY2 | 35 | 输入 | 内部上拉，按下 = 低电平 |
| LED2 绿 | 32 | 输出 | 低电平有效，0 = 亮 |
| LED3 红 | 33 | 输出 | 低电平有效，0 = 亮 |

> ⚠️ GPIO6–11 被 SPI Flash 占用，不可用。

---

## 音频升级说明

Week 2 将音频输出从 **PWM 蜂鸣器** 升级为 **MAX98357A I2S 功放 + 喇叭**。

| 对比项 | PWM 蜂鸣器 | MAX98357A I2S 功放 |
|:-------|:-----------|:-------------------|
| 信号类型 | 方波 | 16-bit PCM 正弦波 |
| 音质 | 谐波丰富、刺耳 | 平滑、音准干净 |
| 驱动方式 | GPIO25 PWM | I2S 总线（GPIO16/17/25）|
| 外设 | 压电蜂鸣器 | 小喇叭 |
| 扩展性 | 仅单音 | 支持复杂波形、多采样率 |

**为什么升级？**
- 方波含有大量高次谐波，听感尖锐；正弦波基频纯净，更适合音乐演示。
- I2S 是数字音频标准接口，为后续旋律、采样播放预留空间。
- MAX98357A 内置 D 类功放，可直接驱动喇叭，无需额外驱动电路。

---

## AI 编程助手选型

| 选项                    | 说明                    | 工具链实现建议         |
| ----------------------- | ----------------------- | ---------------------- |
| Claude Code             | 功能成熟，支持 MCP 扩展 | 实现 MCP 服务器        |
| Codex                   | OpenAI 生态             | 编写 Codex 兼容插件    |
| Zcode                   | 开源环境                | 编写 Zcode 扩展        |
| OpenCode + DeepSeek API | 开源 + 低成本           | 编写 OpenCode 工具扩展 |

---

## Week 1 完成情况（07/06 — 07/12）

### 硬件分析与文档

| 任务                   | 产出文件                                                                         |
| ---------------------- | -------------------------------------------------------------------------------- |
| 解析原理图 / PCB / BOM | `hardware/schematic.pdfhardware/pcb.pdf``hardware/MCPiano_硬件资源分析.xlsx` |
| 编写硬件分析文档       | `hardware/bom_analysis.md`                                                     |

### 环境搭建与固件烧录

| 任务                    | 状态                                     |
| ----------------------- | ---------------------------------------- |
| 安装 Python 3.14 + pip  | ✅                                       |
| 创建 venv 虚拟环境      | ✅`.venv/`                             |
| 安装 esptool + pyserial | ✅                                       |
| 下载 MicroPython 固件   | ✅`ESP32_GENERIC-20240602-v1.23.0.bin` |
| 擦除并烧录 Flash        | ✅ ESP32-D0WD-V3 已确认                  |
| 验证 REPL               | ✅`>>>` 提示符正常                     |

### 外设测试与验证

| 测试项               | 脚本                       | 验证状态                      |
| -------------------- | -------------------------- | ----------------------------- |
| 按键 KEY1 / KEY2     | `tests/test_button.py`   | ✅ 通过                       |
| 9 键手动按压         | `tests/test_buttons_9key.py` | ✅ 通过                       |
| LED 绿 / 红          | `tests/test_led.py`      | ⏳ 未跑（面包板接线后需补测） |
| MAX98357A I2S 功放 | `tests/test_max98357a.py` | ✅ 通过                       |
| 9 键钢琴系统         | `tests/test_piano_v1.py` | ⏳ 待硬件验证                 |
| ~~蜂鸣器七音阶~~   | `tests/test_buzzer.py`   | ~~✅ 通过~~（已废弃，PWM 方案） |

### 工具链前期准备

| 文档                      | 路径                               |
| ------------------------- | ---------------------------------- |
| mini-claude-code 阅读笔记 | `docs/mini_claude_code_notes.md` |
| KimiCode MCP 扩展机制详解 | `docs/toolchain_proposal.md`     |

### 仓库初始化

| 任务                     | 状态                                                |
| ------------------------ | --------------------------------------------------- |
| 标准目录结构创建         | ✅`piano/` `toolchain/` `tests/` `docs/` 等 |
| Git 初始化 + 首次 commit | ✅`180b9d7`                                       |
| `README.md` 创建       | ✅ 已提交                                           |
| `.gitignore` 配置      | ✅ 排除`.venv/` `*.bin` `本地文件/`           |

---

## Week 2 进行中（07/13 — 07/19）

### 数字钢琴核心 v1

| 任务 | 产出文件 | 状态 |
|:-----|:---------|:----:|
| MAX98357A I2S 功放驱动 | `piano/i2s_audio.py` | ✅ 已验证 |
| 9 键扫描模块 | `piano/buttons.py` | ✅ 已验证 |
| 钢琴状态机（音阶/八度） | `piano/piano.py` | ✅ 已完成 |
| 上电自动运行入口 | `piano/main.py` | ✅ 已完成 |
| 功放独立测试 | `tests/test_max98357a.py` | ✅ 通过 |
| 9 键手动检测 | `tests/test_buttons_9key.py` | ✅ 通过 |
| 钢琴系统综合测试 | `tests/test_piano_v1.py` | ⏳ 待验证 |

### 关键硬件接线（已确认）

- **MAX98357A**：VIN→5V, GND→GND, SD_MODE→VIN, GAIN→VIN, BCLK→GPIO16, LRCK→GPIO17, DIN→GPIO25
- **9 个按键**：GPIO23/22/21/19/18/14/12/34/35 → 按键 → GND
- **LED**：本次暂不安装（无 330Ω 限流电阻）

---

## 项目里程碑

| 阶段   | 时间           | 主题                      | 核心产出                     |
| ------ | -------------- | ------------------------- | ---------------------------- |
| 第一周 | 07/06 — 07/12 | 硬件认知与 AI 协作入门    | 硬件分析文档 + 外设测试代码  |
| 第二周 | 07/13 — 07/19 | 数字钢琴核心 + 工具链架构 | 可运行数字钢琴 v1 + 技术方案 |
| 第三周 | 07/20 — 07/26 | 工具链基础功能开发        | 6 项基本工程能力可用         |
| 第四周 | 07/27 — 08/02 | 工具链集成与闭环验证      | AI 自主操控 ESP32 完整演示   |
| 第五周 | 08/03 — 08/09 | 系统完善与项目收尾        | 最终演示 + 技术报告          |

---

## 教学目标

1. **硬件文档解读能力** — 阅读原理图、PCB 版图、BOM
2. **嵌入式软件设计能力** — 模块化系统架构
3. **AI 协作开发能力** — 高效使用 AI 编程助手
4. **开发者工具与基础设施设计能力** — MCP / 插件扩展机制
5. **系统调试与问题解决能力** — 结构化调试方法
6. **技术沟通与工程文档能力**
7. **持续学习与批判性思维**

---

## 学术诚信

- 工程师负最终责任，每一行代码都必须被完全理解
- 硬件验证是唯一标准，AI 生成的代码必须在实际硬件上验证通过
- 如实记录 AI 贡献与不足
- 禁止抄袭、禁止伪造闭环验证演示

---

 *项目进行中，逐步更新……*
