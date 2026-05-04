---
name: bilibili-research
description: Use when user wants to analyze a Bilibili video: extract subtitles/transcript, generate outline, identify key points, fact-check claims, and produce a research report. Triggers on Bilibili URLs (bilibili.com, b23.tv) with analysis/intent keywords like "analyze", "研究", "提取", "outline", "summary".
version: 1.0.0
---

# Bilibili 视频研究助手

从 Bilibili 视频生成研究报告：提取字幕/转录、分析要点、核查事实、提供扩展阅读。

## Prerequisites

- Python 3.10+
- Virtual environment with skill dependencies
- Environment variable `OPENAI_API_BASE` (for GLM) or `ANTHROPIC_API_KEY`

## Directory Convention

```
~/.cache/whisper/                 # Whisper 模型（与 podcast skill 共享）
~/.longerian/
├── venv/bilibili-research/       # Skill 虚拟环境（运行时）
├── data/bilibili-research/       # 音频、字幕、报告输出
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

### Step 1: Extract Content (Agent)

Use the extractor module to get video info and check for subtitles:

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

### Step 2: Transcribe if Needed (Agent)

If no subtitles found, transcribe audio using shared Whisper module:

```python
from shared.whisper_wrapper import transcribe

transcription = transcribe(result.audio_path, language='zh')
transcript = transcription['text']
```

**Note**: Uses Whisper models from `~/.cache/whisper/` (shared with podcast-transcribe-whisper). Models auto-download on first use.

### Step 3: Analyze Content (Agent)

Extract outline, core points, entities, and verifiable claims:

```python
from shared.analyzer import analyze_content

analysis = analyze_content(
    transcript=transcript,
    title=result.title,
    metadata={'uploader': result.uploader, 'url': url}
)
```

Returns:
- `outline`: 5-7 content outline points
- `core_points`: 3-5 key insights
- `key_entities`: people, places, terms
- `verifiable_claims`: statements for fact-checking
- `keywords`: for extended reading search
- `summary`: one-line summary

### Step 4: Fact Check (Optional)

For each verifiable claim, use web search to verify:

1. Search claim statement on web
2. Analyze search results for supporting evidence
3. Record verification status, confidence, evidence URLs

### Step 5: Extended Reading (Optional)

Search for related materials based on keywords:

1. Construct search query from top keywords
2. Fetch 3-5 most relevant results
3. Record title, URL, source, relevance score

### Step 6: Generate Report

```python
from shared.report import generate_html_report, open_report, ReportData

report_data = ReportData(
    video_info={'title': ..., 'uploader': ..., 'duration_str': ..., 'url': ...},
    analysis=analysis.__dict__,
    fact_checks=[...],
    related_reading=[...],
    generated_at=timestamp
)

report_path = generate_html_report(report_data)
open_report(report_path)  # Opens in browser
```

## CLI Usage

**使用虚拟环境运行：**
```bash
# 激活环境后运行
source ~/.longerian/venv/bilibili-research/bin/activate
python3 skills/bilibili_research/bilibili_research.py "https://www.bilibili.com/video/BV..."

# 或直接运行
~/.longerian/venv/bilibili-research/bin/python3 skills/bilibili_research/bilibili_research.py "https://www.bilibili.com/video/BV..."
```

Options:
- `--cookies PATH` — cookies.txt for member videos
- `--no-fact-check` — Skip fact-checking (faster)
- `--no-report` — Skip HTML report generation

## Error Handling

| Scenario | Solution |
|----------|----------|
| Video requires login | Use `--cookies` with browser-exported cookies.txt |
| No subtitles + audio extraction fails | Prompt user to provide cookies or skip video |
| Whisper not installed | `pip install openai-whisper modelscope` |
| Transcription slow (no GPU) | Warn user: ~1 min per 10 min of audio |
| Fact-check API fails | Continue without fact-checking, note in report |
| Member video blocked | Prompt for cookies or skip |

## Multi-Part Videos (多 P 视频)

Bilibili videos may have multiple parts (P1, P2, ...).

**Detection**: Check video info for `parts > 1`

**User Choice**:
- `all` — Process all parts, merge into one report
- `1` — Process only part 1
- `1,3` — Process specific parts

**Default**: Process part 1 only

## Output Example

```
📺 正在处理视频: BV1xx411c7XD

🔍 正在提取内容...
   标题: [视频标题]
   UP主: [UP主名称]
   时长: 15分30秒
   字幕: 有

🧠 正在分析内容...
   ✅ 提取 6 个大纲要点
   ✅ 提取 4 个核心观点
   ✅ 识别 8 个关键实体

🔍 正在核查事实...
   [1/3] [claim preview]...
   [2/3] [claim preview]...
   [3/3] [claim preview]...

📄 正在生成报告...
   ✅ 报告已生成: ~/.longerian/data/bilibili-research/report_20260503_143022.html

🌐 正在打开浏览器...

==================================================
📊 分析完成
==================================================
📝 大纲: 6 个要点
💡 核心观点: 4 条
🔍 事实核查: 3 条
📚 关键词: 7 个

📌 [一句话总结]
```

## Runtime Environment

This skill uses an isolated Python virtual environment:

```bash
# 激活 skill 虚拟环境
source ~/.longerian/venv/bilibili-research/bin/activate

# 或直接运行
~/.longerian/venv/bilibili-research/bin/python3 <script>
```

## Installation

**自动安装（推荐）：**
```bash
# 运行环境设置脚本
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

**API 配置：**
```bash
# GLM (OpenAI-compatible)
export OPENAI_API_BASE="https://open.bigmodel.cn/api/paas/v4/"
export OPENAI_API_KEY="your-glm-api-key"

# 或 Anthropic Claude
export ANTHROPIC_API_KEY="sk-..."
```
