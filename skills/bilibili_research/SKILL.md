---
name: bilibili-research
description: Use when user wants to analyze a Bilibili video: extract subtitles/transcript for AI agent analysis. Triggers on Bilibili URLs (bilibili.com, b23.tv) with analysis/intent keywords like "analyze", "研究", "提取", "outline", "summary".
version: 1.0.0
---

# Bilibili 视频研究助手

从 Bilibili 视频提取字幕/转录文本，供 AI Agent 分析。

## Prerequisites

- Python 3.10+
- Virtual environment with skill dependencies

## Directory Convention

```
~/.cache/whisper/                 # Whisper 模型
~/.longerian/
├── venv/bilibili-research/       # Skill 虚拟环境
├── data/bilibili-research/       # 音频、转录文件输出
└── scripts/                      # 共享脚本
```

Setup:
```bash
# 运行环境设置脚本（自动创建虚拟环境并安装依赖）
./skills/bilibili_research/setup_env.sh

# 创建输出目录
mkdir -p ~/.longerian/data/bilibili-research
```

## Pipeline

### Step 1: Extract Content

```python
from skills.bilibili_research.extractor import extract

result = extract(
    url="https://www.bilibili.com/video/BV...",
    output_dir="~/.longerian/data/bilibili-research",
    cookies_path=None  # Optional: for member videos
)
```

Returns:
- `title`, `uploader`, `duration`
- `has_subtitles`: bool
- `transcript`: str (if subtitles available)
- `audio_path`: str (if no subtitles)

### Step 2: Transcribe if Needed

If no subtitles found, transcribe audio using Whisper:

```python
from shared.whisper_wrapper import transcribe

transcription = transcribe(result.audio_path, language='zh')
transcript = transcription['text']
```

**Note**: Uses Whisper models from `~/.cache/whisper/`. Models auto-download on first use.

### Step 3: Analyze with AI Agent

The script generates two files:

```bash
python3 skills/bilibili_research/bilibili_research.py "https://www.bilibili.com/video/BV..."
```

Output files:
- `transcript_{VIDEO_ID}_{TIMESTAMP}.txt` — 原始转录文本
- `prompt_{VIDEO_ID}_{TIMESTAMP}.txt` — AI 分析提示模板

**让 AI Agent 分析:**
1. 读取 `prompt_*.txt` 文件，其中已包含完整转录和分析提示
2. AI 直接按提示结构输出分析报告

**报告结构:**
```markdown
## 一、核心主题
## 二、关键信息点（含具体数据）
## 三、技术/概念详解
## 四、数据汇总（表格）
## 五、对比分析（表格）
## 六、风险与机会
## 七、结论
```

## CLI Usage

```bash
# 基本用法
python3 skills/bilibili_research/bilibili_research.py "https://www.bilibili.com/video/BV..."

# 会员视频（需要 cookies）
python3 skills/bilibili_research/bilibili_research.py "https://www.bilibili.com/video/BV..." --cookies cookies.txt
```

Options:
- `--cookies PATH` — cookies.txt for member videos

## Error Handling

| Scenario | Solution |
|----------|----------|
| Video requires login | Use `--cookies` with browser-exported cookies.txt |
| No subtitles + audio extraction fails | Prompt user to provide cookies or skip video |
| Whisper not installed | `pip install openai-whisper modelscope` |
| Transcription slow (no GPU) | Warn user: ~1 min per 10 min of audio |
| Member video blocked | Prompt for cookies or skip |

## Output Example

```
📺 正在处理视频: BV1xx411c7XD

🔍 正在提取内容...
   标题: [视频标题]
   UP主: [UP主名称]
   时长: 15分30秒
   字幕: 有

📝 转录已保存到: ~/.longerian/data/bilibili-research/transcript_BV1xx411c7XD_20260504_120000.txt
📏 转录文本: 12500 字符

💡 下一步: 让 AI 分析此转录文件
   可使用 Read 工具读取: ~/.longerian/data/bilibili-research/transcript_BV1xx411c7XD_20260504_120000.txt
```

## Installation

**自动安装（推荐）：**
```bash
./skills/bilibili_research/setup_env.sh
```

**手动安装：**
```bash
# 安装外部工具
brew install yt-dlp ffmpeg  # macOS
# or
apt install yt-dlp ffmpeg   # Linux

# 创建虚拟环境并安装依赖
python3 -m venv ~/.longerian/venv/bilibili-research
source ~/.longerian/venv/bilibili-research/bin/activate
pip install -r requirements.txt
```
