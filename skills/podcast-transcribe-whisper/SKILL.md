---
name: podcast-transcribe-whisper
description: Use when user wants to transcribe a podcast audio using local Whisper model. Triggers on requests like "transcribe podcast", "extract podcast transcript", "podcast to text", or when given a podcast URL (xiaoyuzhoufm.com, ximalaya.com) with transcription intent.
version: 1.0.0
---

# Podcast Transcription with Whisper (Local)

Transcribe podcast audio locally using OpenAI Whisper large-v3-turbo model. Complete pipeline: download audio → transcribe → organize knowledge → export Markdown.

## Prerequisites

- Python 3.x with `openai-whisper` installed
- Sufficient disk space (~1.5GB for model)
- **GPU acceleration (recommended)**: NVIDIA GPU with CUDA

**Verify GPU:**
```bash
python -c "import torch; print(torch.cuda.is_available())"  # Should be True
python -c "import torch; print(torch.cuda.get_device_name(0))"  # Your GPU name
```

**Install PyTorch with CUDA (Python 3.12 recommended):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Whisper auto-detects and uses GPU if available (~25x faster than CPU).

## Directory Convention

```
~/.cache/whisper/             # Whisper models (shared across skills)
~/.longerian/
├── scripts/                 # Python scripts
└── data/podcast/            # Audio files + transcript output
```

Setup:
```bash
mkdir -p ~/.longerian/{scripts,data/podcast}
```

## Pipeline

### Step 1: Extract Audio URL from Podcast Page

Use web-reader to fetch the podcast page and extract the RSS-authorized audio URL.

For Xiaoyuzhou (小宇宙) podcasts:
1. Fetch the podcast page with web-reader
2. Find the RSS feed URL from the page source
3. Extract the `<enclosure url="...">` from the RSS feed - this is the authorized URL with `jt` parameter

For direct CDN URLs (xmcdn.com), use them for local download only (not for API access).

```bash
curl -sL -o ~/.longerian/data/podcast/episode.m4a "<CDN_DIRECT_URL>"
```

### Step 2: Ensure Whisper Model Ready

Model location: `~/.cache/whisper/` (Whisper default cache, shared with bilibili skill)

Whisper auto-downloads models on first use. To check available models:

```bash
ls ~/.cache/whisper/
```

Models:
- `base.pt` (~145 MB) - Fast, good for quick tests
- `large-v3-turbo.pt` (~1.2 GB) - Best accuracy (recommended)

### Step 3: Run Whisper Transcription

Write script to `~/.longerian/scripts/transcribe.py`:

```python
import os, whisper, torch

AUDIO_PATH = os.path.expanduser('~/.longerian/data/podcast/episode.m4a')
OUTPUT_DIR = os.path.expanduser('~/.longerian/data/podcast')

os.makedirs(OUTPUT_DIR, exist_ok=True)

# GPU detection
if torch.cuda.is_available():
    print(f"[GPU] Using CUDA: {torch.cuda.get_device_name(0)}")
else:
    print("[WARNING] CUDA not available, using CPU (slow)")

# Use model size: tiny, base, small, medium, large-v3-turbo
# Whisper auto-loads from ~/.cache/whisper/
model = whisper.load_model('large-v3-turbo')
result = model.transcribe(AUDIO_PATH, language='zh', verbose=True)

output_path = os.path.join(OUTPUT_DIR, 'whisper_transcript.txt')
with open(output_path, 'w', encoding='utf-8') as f:
    for seg in result['segments']:
        f.write(seg['text'] + '\n')

print(f"Transcription saved to {output_path}")
```

Execute:
```bash
python3 ~/.longerian/scripts/transcribe.py
```

### Step 4: Organize Knowledge Points

Read the transcript from `~/.longerian/data/podcast/whisper_transcript.txt` and organize into structured knowledge points:

- Core thesis / main arguments
- Key knowledge points by category
- Notable quotes
- Comparison tables (old vs new paradigms)
- Timeline of discussion topics

### Step 5: Export Markdown

Save to current working directory:
```
{podcast-title}-知识点整理.md
{podcast-title}-Whisper转录.md
```

## Known Limitations

- **No punctuation**: Whisper Chinese output lacks punctuation marks
- **Name errors**: May misrecognize names (e.g., 任鑫→任心, 徐文浩→徐丰浩)
- **CPU slow**: ~20 minutes for 1.5h audio on CPU
- **One continuous block**: No paragraph/speaker segmentation

## Tips

- Models are auto-downloaded to `~/.cache/whisper/` on first use
- For better quality with punctuation, consider using MiMo API skill instead
- **GPU acceleration**: ~25x faster than CPU (1.5h audio → ~4 min on GPU)
- Use Python 3.12 for best PyTorch CUDA support
