# Douyin Video Transcription Skill

Transcribe Douyin (抖音) videos using Whisper with GPU acceleration.

## Quick Start

```bash
# Download and transcribe a Douyin video
node douyin_download_and_transcribe.js "https://www.douyin.com/jingxuan?modal_id=7637131372982149285"

# Or transcribe an already downloaded video
python douyin_transcribe.py path/to/video.mp4
```

## Features

- **GPU Acceleration** - Uses RTX 4070 SUPER for ~25x real-time transcription
- **Automatic Download** - Fetches video URL from Douyin using Playwright
- **Chinese Optimized** - Uses Whisper large-v3-turbo model for best Chinese accuracy
- **Multiple Outputs** - Plain text and timestamped segments

## Requirements

- Python 3.12 (for PyTorch CUDA support)
- Node.js with playwright
- NVIDIA GPU with CUDA
- ffmpeg

## Installation

```bash
# Install Python dependencies (Python 3.12)
pip install openai-whisper torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Node dependencies
npm install playwright

# Install ffmpeg
choco install ffmpeg
```

## Output Files

Transcripts are saved to `~/.longerian/data/douyin/`:

- `{timestamp}-transcript.txt` - Plain text transcript
- `{timestamp}-segments.txt` - With timestamps
- `douyin_{timestamp}.mp4` - Downloaded video

## Performance

On RTX 4070 SUPER:
- 2.5 min video → ~6 seconds transcription
- ~25x real-time speed

## Troubleshooting

**CUDA not available?**
- Make sure you're using Python 3.12 (not 3.14)
- Reinstall PyTorch with CUDA: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`

**Video URL not found?**
- Douyin URLs expire quickly
- Try refreshing the page
- Check your internet connection

**Poor transcript quality?**
- Original video audio quality matters
- Background music/noise affects accuracy
- Consider using larger models (large-v3-turbo is recommended)
