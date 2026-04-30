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

## Execution Convention

All Python scripts in this skill should be:
1. Written to `/tmp/longerian_skill/` as `.py` files
2. Executed via shell: `python3 /tmp/longerian_skill/xxx.py`
3. If default python3 fails (version conflict), try `python3.11` explicitly

Example:
```bash
mkdir -p /tmp/longerian_skill
cat > /tmp/longerian_skill/transcribe.py << 'PYEOF'
# python code here
PYEOF
python3 /tmp/longerian_skill/transcribe.py
```

## Model Storage

Model stored at: `~/.longerian/models/whisper/` (persistent, survives reboot, agent-agnostic)

Auto-detect before transcription:
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
# Download audio via CDN direct URL (works for local use)
curl -sL -o /tmp/podcast_episode.m4a "<CDN_DIRECT_URL>"
```

### Step 2: Ensure Whisper Model Ready

Auto-check and download if needed (see Model Storage section above). Model path: `~/.longerian/models/whisper/iic/Whisper-large-v3-turbo/large-v3-turbo.pt`

### Step 3: Run Whisper Transcription

Write script to `/tmp/longerian_skill/transcribe.py`:

```python
import os, whisper

MODEL_PATH = os.path.expanduser('~/.longerian/models/whisper/iic/Whisper-large-v3-turbo/large-v3-turbo.pt')
AUDIO_PATH = '/tmp/podcast_episode.m4a'
OUTPUT_DIR = '/tmp/podcast_transcript'

os.makedirs(OUTPUT_DIR, exist_ok=True)

model = whisper.load_model(MODEL_PATH)
result = model.transcribe(AUDIO_PATH, language='zh', verbose=True)

with open(os.path.join(OUTPUT_DIR, 'transcript.txt'), 'w', encoding='utf-8') as f:
    for seg in result['segments']:
        f.write(seg['text'] + '\n')

print(f"Transcription saved to {OUTPUT_DIR}/transcript.txt")
```

Execute:
```bash
python3 /tmp/longerian_skill/transcribe.py
```

### Step 4: Organize Knowledge Points

Read the transcript and organize into structured knowledge points:

- Core thesis / main arguments
- Key knowledge points by category
- Notable quotes
- Comparison tables (old vs new paradigms)
- Timeline of discussion topics

### Step 5: Export Markdown

Save to current working directory with naming convention:
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
