---
name: podcast-transcribe-whisper
description: Use when user wants to transcribe a podcast audio using local Whisper model. Triggers on requests like "transcribe podcast", "extract podcast transcript", "podcast to text", or when given a podcast URL (xiaoyuzhoufm.com, ximalaya.com) with transcription intent.
version: 1.0.0
---

# Podcast Transcription with Whisper (Local)

Transcribe podcast audio locally using OpenAI Whisper large-v3-turbo model. Complete pipeline: download audio → transcribe → organize knowledge → export Markdown.

## Prerequisites

- Python 3.11+ with `openai-whisper` installed
- `modelscope` package for model download (faster in China)
- Sufficient disk space (~1.5GB for model)

## Directory Convention

All files use `~/.longerian/` (persistent, agent-agnostic):

```
~/.longerian/
├── models/whisper/          # Whisper model (auto-download)
├── scripts/                 # Python scripts
└── data/podcast/            # Audio files + transcript output
```

Setup:
```bash
mkdir -p ~/.longerian/{scripts,data/podcast,models/whisper}
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

Model path: `~/.longerian/models/whisper/iic/Whisper-large-v3-turbo/large-v3-turbo.pt`

Write script to `~/.longerian/scripts/ensure_model.py`:

```python
import os

MODEL_DIR = os.path.expanduser('~/.longerian/models/whisper/iic/Whisper-large-v3-turbo')
MODEL_PATH = os.path.join(MODEL_DIR, 'large-v3-turbo.pt')

if not os.path.exists(MODEL_PATH):
    print("Downloading Whisper model from ModelScope...")
    os.makedirs(os.path.expanduser('~/.longerian/models/whisper'), exist_ok=True)
    from modelscope import snapshot_download
    snapshot_download('iic/Whisper-large-v3-turbo', cache_dir=os.path.expanduser('~/.longerian/models/whisper'))
    print("Model downloaded.")
else:
    print("Model ready.")
```

Execute:
```bash
python3 ~/.longerian/scripts/ensure_model.py
```

### Step 3: Run Whisper Transcription

Write script to `~/.longerian/scripts/transcribe.py`:

```python
import os, whisper

MODEL_PATH = os.path.expanduser('~/.longerian/models/whisper/iic/Whisper-large-v3-turbo/large-v3-turbo.pt')
AUDIO_PATH = os.path.expanduser('~/.longerian/data/podcast/episode.m4a')
OUTPUT_DIR = os.path.expanduser('~/.longerian/data/podcast')

os.makedirs(OUTPUT_DIR, exist_ok=True)

model = whisper.load_model(MODEL_PATH)
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

If default python3 fails (version conflict), try `python3.11` explicitly.

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
- **CPU slow**: ~20 minutes for 1.5h audio on CPU; GPU significantly faster
- **One continuous block**: No paragraph/speaker segmentation

## Tips

- If HuggingFace download fails (SSL/network), use ModelScope mirror
- If `openai-whisper` import fails, check Python version (needs 3.11)
- For better quality with punctuation, consider using MiMo API skill instead
