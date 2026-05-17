---
name: bilibili-research
description: Use when user wants to analyze a Bilibili video or extract transcript for AI analysis. Triggers on Bilibili URLs (bilibili.com, b23.tv) or when keywords like "analyze", "研究", "提取", "transcribe" are provided.
version: 2.0.0
---

# Bilibili 视频研究助手

从 Bilibili 视频提取字幕/转录文本，支持三种模式：
1. **报告模式**（默认）：生成完整的 HTML/Markdown 报告，包含图表和 AI 分析
   - 自适应报告结构（根据内容类型自动调整章节）
   - 支持公司分析、技术教程、评论观点、新闻资讯、访谈对话等
2. **Agent 模式**：提取转录文本供 AI Agent 分析
3. **提示模式**：仅生成 AI 分析提示模板

## Prerequisites

- Python 3.10+ (Python 3.12 recommended for GPU acceleration)
- Virtual environment with skill dependencies

**Agent/提示模式**:
- yt-dlp（视频提取）
- ffmpeg（音频处理，可选）
- openai-whisper（转录，无字幕时需要）

**报告模式**（额外需要）:
- LLM API key (`OPENAI_API_KEY` 或 `ZHIPU_API_KEY`)
- matplotlib（图表生成）
- openai（API 调用）

**GPU 加速（可选但推荐）**:
- NVIDIA GPU with CUDA
- PyTorch with CUDA support

```bash
# Verify GPU
python -c "import torch; print(torch.cuda.is_available())"

# Install PyTorch with CUDA (Python 3.12)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

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

If no subtitles found, transcribe audio using Whisper (GPU-accelerated):

```python
from skills.bilibili_research.whisper_wrapper import transcribe

transcription = transcribe(result.audio_path, language='zh', verbose=True)
transcript = transcription['text']
```

**Note**: Uses Whisper `large-v3-turbo` model from `~/.cache/whisper/` (shared with douyin-transcribe). Auto-detects and uses GPU if available.

**Model options**: `tiny`, `base`, `small`, `medium`, `large-v3-turbo` (default, best accuracy)

### Step 3: Choose Analysis Mode

**Agent 模式（默认）** - 提取转录供 AI Agent 分析:

```bash
python3 bilibili_research.py "https://www.bilibili.com/video/BV..."
```

Output:
- `transcript_{VIDEO_ID}_{TIMESTAMP}.txt` — 原始转录文本
- `prompt_{VIDEO_ID}_{TIMESTAMP}.txt` — AI 分析提示模板

**报告模式** - 生成完整 HTML/Markdown 报告:

```bash
# 需要设置 OPENAI_API_KEY 或 ZHIPU_API_KEY 环境变量
python3 bilibili_research.py "https://www.bilibili.com/video/BV..." --report
```

Output:
- `transcript_{VIDEO_ID}_{TIMESTAMP}.txt` — 原始转录文本
- `report_{VIDEO_ID}_{TIMESTAMP}.html` — HTML 报告（含图表）
- `report_{VIDEO_ID}_{TIMESTAMP}.md` — Markdown 报告
- `chart_*.png` — 数据可视化图表

**提示模式** - 仅生成分析提示模板:

```bash
python3 bilibili_research.py "https://www.bilibili.com/video/BV..." --prompt-only
```

Output:
- `prompt_{VIDEO_ID}_{TIMESTAMP}.txt` — AI 分析提示模板

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
# 报告模式（默认）- 生成完整 HTML/Markdown 报告（需要 LLM API）
python3 bilibili_research.py "https://www.bilibili.com/video/BV..."

# Agent 模式 - 提取转录供 AI Agent 分析
python3 bilibili_research.py "https://www.bilibili.com/video/BV..." --agent-mode

# 提示模式 - 仅生成分析提示模板
python3 bilibili_research.py "https://www.bilibili.com/video/BV..." --prompt-only

# 会员视频（需要 cookies）
python3 bilibili_research.py "https://www.bilibili.com/video/BV..." --cookies cookies.txt

# 报告模式 + 在浏览器中打开
python3 bilibili_research.py "https://www.bilibili.com/video/BV..." --open

# 使用基础分析（更快，但无详细章节和图表）
python3 bilibili_research.py "https://www.bilibili.com/video/BV..." --basic
```

**Options:**
- `--cookies PATH` — cookies.txt for member videos
- `--agent-mode` — Agent mode: extract transcript for AI Agent analysis (default is report mode)
- `--prompt-only` — Prompt mode: only generate analysis prompt template
- `--no-charts` — Skip chart generation in report mode
- `--basic` — Use basic analysis (faster, no detailed content)
- `--model MODEL` — LLM model for report generation (default: glm-4-flash)
- `--open` — Open HTML report in browser after generation

## Error Handling

| Scenario | Solution |
|----------|----------|
| Video requires login | Use `--cookies` with browser-exported cookies.txt |
| No subtitles + audio extraction fails | Prompt user to provide cookies or skip video |
| Whisper not installed | `pip install openai-whisper modelscope` |
| Transcription slow (no GPU) | Install PyTorch with CUDA for ~25x speedup |
| Member video blocked | Prompt for cookies or skip |

**GPU Performance**:
- RTX 4070 SUPER: ~25x real-time speed
- CPU fallback: ~1 min per 10 min of audio

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
