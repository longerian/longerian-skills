---
name: douyin-transcribe
description: Use when transcribing Douyin (抖音) videos to text. Triggers on douyin.com URLs or keywords: 抖音转录、抖音视频转文字、提取抖音字幕、transcribe douyin. Supports batch processing.
version: 2.0.0
---

# Douyin Video Transcription

## Overview

Transcribe Douyin (TikTok China) videos to text using Whisper with GPU acceleration. Automatically downloads videos, extracts audio, transcribes with Chinese-optimized models, and generates formatted Markdown reports with keywords.

## When to Use

```dot
digraph when_douyin {
    "Have Douyin URL?" [shape=diamond];
    "Need Chinese text?" [shape=diamond];
    "Single or Batch?" [shape=diamond];
    "Use this skill" [shape=box];

    "Have Douyin URL?" -> "Need Chinese text?";
    "Need Chinese text?" -> "Use this skill" [label="Yes"];
    "Have Douyin URL?" -> "Use this skill" [label="Yes, batch URLs"];
}
```

**Triggers:** `douyin.com` URL, keywords (抖音转录、抖音视频转文字、提取抖音字幕、transcribe douyin), request for Douyin subtitles/speech extraction.

**When NOT to use:** Non-Douyin platforms, English-only content, real-time requirements.

## Quick Reference

| Command | Mode | Use When |
|---------|------|----------|
| `node douyin_transcribe.js` | Interactive | User wants to paste URL(s) manually |
| `node douyin_transcribe.js "URL"` | Single URL | URL provided directly |
| `node douyin_transcribe.js --batch "url1,url2"` | Batch | Multiple URLs at once |

**Supported URL formats:**
- `https://www.douyin.com/video/{video_id}`
- `https://www.douyin.com/user/{user_id}?modal_id={video_id}`
- `https://www.douyin.com/jingxuan?modal_id={video_id}`

## Output

**Location**: `~/.longerian/data/douyin/`

| File | Content |
|------|---------|
| `douyin_{timestamp}-report.md` | Keywords, transcript with timestamps |
| `douyin_{timestamp}-transcript.txt` | Plain text |
| `douyin_{timestamp}.mp4` | Downloaded video |

**Report includes**: video metadata, keywords, full transcript with enhanced punctuation, segmented transcript with timestamps.

## Prerequisites

**Required:**
- Python 3.12+ (for PyTorch CUDA support - 3.14 lacks CUDA builds)
- NVIDIA GPU with CUDA drivers
- Node.js with `playwright`
- `ffmpeg` for audio processing

**Verify GPU:**
```bash
python -c "import torch; print(torch.cuda.is_available())"  # Should be True
python -c "import torch; print(torch.cuda.get_device_name(0))"  # Your GPU name
```

**Install:**
```bash
# Python 3.12 (CUDA)
pip install openai-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
# Node.js
npm install playwright && npx playwright install
# ffmpeg
choco install ffmpeg
```

## Performance

RTX 4070 SUPER: 2.5 min video → ~6 seconds (~25x real-time). CPU would take ~112 seconds.

## Features

**v2.0**: Enhanced punctuation, keyword extraction, batch processing. See IMPLEMENTATION.md for details.

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Wrong Python version | CUDA not available errors | Use Python 3.12, not 3.14 |
| Expired video URL | "Video URL not found" | Fetch fresh URL (Douyin signatures expire) |
| Missing ffmpeg | Audio extraction fails | Install ffmpeg via choco/brew |
| Poor transcription quality | Garbled text | Check original audio quality, background noise affects accuracy |

## Known Limitations

- Douyin video URLs expire quickly - must fetch fresh each time
- Punctuation is heuristic-based, not 100% accurate
- Background music/noise affects transcription accuracy
- Name recognition may need manual correction (e.g., 老川→老船, 检藏→减仓)
- Batch processing is sequential, not parallel (to avoid overwhelming network/GPU)
- Requires NVIDIA GPU - CPU fallback is much slower

## Implementation

See `IMPLEMENTATION.md` for detailed pipeline steps, code examples, and troubleshooting.
