---
name: douyin-transcribe
description: Use when user wants to transcribe a Douyin (TikTok China) video with manual trigger. Triggers on Douyin URLs (douyin.com) or keywords like "抖音转录", "抖音视频转文字", "提取抖音字幕", "transcribe douyin". Supports batch processing. User will be prompted to paste the video URL(s).
version: 2.0.0
---

# Douyin Video Transcription with Whisper (GPU Accelerated)

**Manual trigger tool**: Run the script, then paste a Douyin URL when prompted. The tool will download the video, transcribe it using Whisper (GPU accelerated), and generate a formatted Markdown report with keyword extraction.

## Quick Start

```bash
cd .agents/skills/douyin-transcribe
node douyin_transcribe.js
```

Then paste a Douyin URL like `https://www.douyin.com/jingxuan?modal_id=7637131372982149285`

**New in v2.0:**
- ✨ **Enhanced punctuation**: Better readability with smart punctuation rules
- 🔄 **Batch processing**: Process multiple URLs at once
- 📌 **Keyword extraction**: Auto-extract keywords and key phrases

## Prerequisites

- **Python 3.12+** (for PyTorch CUDA support)
- **NVIDIA GPU** with CUDA drivers (RTX 4070 SUPER tested)
- **Node.js** with `playwright` installed
- **ffmpeg** for audio processing

## Directory Convention

```
~/.cache/whisper/             # Whisper models (shared across skills)
~/.longerian/
├── scripts/                 # Utility scripts
└── data/douyin/             # Downloaded videos + transcripts + Markdown reports
```

## Pipeline

### Step 1: User Inputs URL(s)

**Interactive mode** (supports batch):
```bash
node douyin_transcribe.js
# Paste multiple URLs separated by spaces
```

**Command line single URL:**
```bash
node douyin_transcribe.js "https://www.douyin.com/video/..."
```

**Command line batch processing:**
```bash
node douyin_transcribe.js --batch "url1,url2,url3"
```

Supported URL formats:
- `https://www.douyin.com/video/{video_id}`
- `https://www.douyin.com/user/{user_id}?modal_id={video_id}`
- `https://www.douyin.com/jingxuan?modal_id={video_id}`

### Step 2: Fetch Video URL with Playwright

Script prompts user to paste Douyin URL. Supported URL formats:
- `https://www.douyin.com/video/{video_id}`
- `https://www.douyin.com/user/{user_id}?modal_id={video_id}`
- `https://www.douyin.com/jingxuan?modal_id={video_id}`

### Step 2: Fetch Video URL with Playwright

Use Playwright to navigate to Douyin page and intercept network responses to find the actual video CDN URL:

```javascript
page.on('response', async (response) => {
  const url = response.url();
  if (url.includes('douyinvod.com') && url.includes('media-video')) {
    mediaUrl = url;  // Found the video URL
  }
});

await page.goto(douyinUrl);
await page.waitForTimeout(15000); // Wait for video to load
```

### Step 3: Download Video

Download using curl:

```bash
curl -L -o ~/.longerian/data/douyin/video.mp4 "{VIDEO_URL}"
```

### Step 4: Transcribe with Whisper (GPU)

Use Python 3.12 with CUDA-enabled PyTorch:

```python
import whisper

model = whisper.load_model('large-v3-turbo')  # Auto-detects GPU
result = model.transcribe('video.mp4', language='zh')
```

### Step 5: Generate Markdown Report with Keywords

Create a comprehensive Markdown report with:
- Video metadata (title, author, duration)
- **📌 Keywords section** (NEW):
  - High-frequency words extracted from transcript
  - Key phrases (industry terms, company names, etc.)
- Full transcript with **enhanced punctuation** (NEW)
  - Smart comma placement for conjunctions
  - Proper punctuation for questions and exclamations
  - Name disambiguation (老黄 → 老黄（黄仁勋）)
- Segmented transcript with timestamps
- Performance statistics

Output: `douyin_{timestamp}-报告.md`

## Enhanced Punctuation Rules (v2.0)

The tool now applies sophisticated punctuation rules:

1. **Conjunctions**: 那么、但是、所以、因为 → 加逗号
2. **Ordinals**: 第一是、其次、再其 → 加冒号
3. **Questions**: 吗呢吧 + 怎么/什么/为什么 → 加问号
4. **Exclamations**: 真的/确实/太 + 哎呀 → 加感叹号
5. **Names**:
   - 老黄 → 老黄（黄仁勋）
   - 老川 → 老川（川普）
   - 库克 → 库克（苹果CEO）
   - 老马 → 老马（马斯克）
   - 雷总 → 雷总（雷军）
6. **Topic separation**: 另起一行处理新话题

## Keyword Extraction (v2.0)

Automatically extracts:

**High-frequency words**: 2-4 character terms with frequency > 1, excluding common stopwords

**Key phrases**:
- English acronyms: GPU, CPU, CPO, AI, ETF
- Industry terms: 光模块、AI芯片、供应链
- Trend descriptions: 大幅增长、快速回调

## Batch Processing (v2.0)

Process multiple Douyin URLs in one command:

```bash
# Interactive batch
node douyin_transcribe.js
# Enter: url1 url2 url3 (space-separated)

# Command line batch
node douyin_transcribe.js --batch "url1,url2,url3"
```

The tool will:
1. Show progress for each video (1/3, 2/3, 3/3)
2. Generate individual reports for each
3. Display summary at the end
4. Offer to open the last report

Create a comprehensive Markdown report with:
- Video metadata (title, author, duration)
- Full transcript with basic punctuation
- Segmented transcript with timestamps
- Performance statistics

Output: `douyin_{timestamp}-报告.md`

## Output Format

The Markdown report includes:

```markdown
# {视频标题}

**作者**: {作者名称}
**转录时间**: 2026-05-16 20:15
**视频时长**: 150.8秒 (2.5分钟)
**转录耗时**: 6.2秒
**处理速度**: 24.3x 实时

---

## 📌 关键词

**高频词**: 英伟达、H200、松绑、阿里、腾讯、关税、供应链
**关键短语**: GPU加速、光模块、AI芯片、供应链、CPO

---

## 完整转录

{带有增强标点的完整转录文本}

---

## 分段转录 (带时间戳)

### [2:30] 第一个片段内容

### [2:45] 第二个片段内容
...
```

## GPU Acceleration

**CRITICAL**: Use Python 3.12+ for PyTorch CUDA support.

Verify GPU:
```python
import torch
print(torch.cuda.is_available())  # Should be True
print(torch.cuda.get_device_name(0))  # Your GPU name
```

**Performance (RTX 4070 SUPER)**:
- 2.5 min video → ~6 seconds transcription
- **~25x real-time speed**
- CPU would take ~112 seconds

## Usage Examples

```bash
# Run the tool
node douyin_transcribe.js

# When prompted, paste URL:
# https://www.douyin.com/jingxuan?modal_id=7637131372982149285

# Output files will be in ~/.longerian/data/douyin/
```

## Known Limitations

- **Douyin URLs expire**: Video URLs have signatures that expire, must fetch fresh each time
- **Punctuation is heuristic**: Enhanced rules improve readability but may not be 100% accurate
- **Background noise**: Music and sound effects can affect accuracy
- **Name errors**: May misrecognize names (老川→老船, 检藏→减仓, etc.) - disambiguation helps but not perfect
- **Keyword extraction**: Simple frequency-based, may miss some context-dependent terms
- **Batch processing**: Sequential execution, not parallel (to avoid overwhelming network/GPU)
- **Requires Python 3.12**: Python 3.14 lacks PyTorch CUDA builds

## Tips

- Always use Python 3.12 for GPU acceleration
- `large-v3-turbo` model gives best accuracy for Chinese
- Report auto-opens in default Markdown viewer after completion
- All output files saved to `~/.longerian/data/douyin/`
- **Batch mode**: Use space-separated URLs in interactive mode for easiest workflow
- **Keywords**: Check the 📌 section first to quickly understand video content
- **Punctuation**: Text is auto-formatted but may need manual polish for publication
