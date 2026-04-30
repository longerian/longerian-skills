---
name: podcast-transcribe-mimo
description: Use when user wants to transcribe a podcast using MiniMax MiMo cloud API. Triggers on requests like "transcribe with MiMo", "MiMo转录", "cloud transcription", or when given a podcast URL with cloud transcription intent. Requires MIMO_API_KEY environment variable.
version: 1.0.0
---

# Podcast Transcription with MiMo API (Cloud)

Transcribe podcast audio via MiniMax MiMo v2.5 cloud API. Faster and higher quality than local Whisper - includes punctuation, paragraph segmentation, and accurate name recognition.

## Prerequisites

- `openai` Python package (`pip install openai`)
- Environment variable `MIMO_API_KEY` set with valid API key
- Audio URL must be cloud-accessible (RSS-authorized URL, NOT CDN direct link)

## Directory Convention

All files use `~/.longerian/` (persistent, agent-agnostic):

```
~/.longerian/
├── scripts/                 # Python scripts
└── data/podcast/            # Transcript output
```

Setup:
```bash
mkdir -p ~/.longerian/{scripts,data/podcast}
```

## Key Difference from Whisper

| Dimension | Whisper (local) | MiMo (cloud) |
|-----------|----------------|--------------|
| Punctuation | None | Complete |
| Segmentation | None | Natural paragraphs |
| Name accuracy | Errors common | Accurate |
| Speed | ~20min (CPU) | ~3min (API) |
| Cost | Free | Token-based |
| URL requirement | Local file | Cloud-accessible URL |

## Critical: Audio URL Format

MiMo API fetches audio from the cloud. The URL must be accessible from external servers.

**Works**: RSS-authorized URL with `jt` parameter
```
https://jt.ximalaya.com//AUDIO_ID.m4a?channel=rss&album_id=XXX&track_id=XXX&uid=XXX&jt=https://aod.cos.tx.xmcdn.com/...
```

**Fails**: CDN direct link (has anti-hotlink/expiry restrictions)
```
https://aod.cos.tx.xmcdn.com/storages/.../AUDIO_ID.m4a
```

If CDN direct URL is used, MiMo will NOT report an error - it will **hallucinate** a transcript from unrelated content. Always verify the URL works before running.

## Pipeline

### Step 1: Extract Audio URL from Podcast Page

Use web-reader to fetch the podcast page and extract the RSS-authorized audio URL.

For Xiaoyuzhou (小宇宙) podcasts:
1. Fetch the podcast page with web-reader
2. Find the RSS feed URL from the page source
3. Extract the full URL from `<enclosure>` tag in RSS feed
4. Verify URL contains `jt=` parameter (required for external API access)

### Step 2: Run MiMo API Transcription

Write script to `~/.longerian/scripts/transcribe_mimo.py`:

```python
from openai import OpenAI
import os

OUTPUT_DIR = os.path.expanduser('~/.longerian/data/podcast')
os.makedirs(OUTPUT_DIR, exist_ok=True)

client = OpenAI(
    api_key=os.environ['MIMO_API_KEY'],
    base_url='https://token-plan-cn.xiaomimimo.com/v1'
)

audio_url = '<RSS_AUTHORIZED_URL>'  # Must have jt= parameter

completion = client.chat.completions.create(
    model='mimo-v2.5',
    messages=[
        {'role': 'system', 'content': 'You are a professional Chinese audio transcription assistant.'},
        {'role': 'user', 'content': [
            {'type': 'input_audio', 'input_audio': {'data': audio_url}},
            {'type': 'text', 'text': '请将这段播客音频逐字转录为文字。保留原始的口语化表达，不要修改或润色内容。只输出转录文字，不要添加任何总结或分析。'}
        ]}
    ],
    max_completion_tokens=64000
)

transcript = completion.choices[0].message.content

# Check completion
if completion.choices[0].finish_reason == 'length':
    print("WARNING: Transcription hit token limit, may be incomplete")

# Save transcript
output_path = os.path.join(OUTPUT_DIR, 'mimo_transcript.txt')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(transcript)

print(f"Transcription saved to {output_path}")
print(f"Characters: {len(transcript)}")
print(f"Tokens - prompt: {completion.usage.prompt_tokens}, completion: {completion.usage.completion_tokens}")
```

Execute:
```bash
python3 ~/.longerian/scripts/transcribe_mimo.py
```

### Step 3: Organize Knowledge Points

Read the transcript from `~/.longerian/data/podcast/mimo_transcript.txt` and organize into structured knowledge points:

- Core thesis / main arguments
- Key knowledge points by category
- Notable quotes
- Comparison tables (old vs new paradigms)
- Timeline of discussion topics

### Step 4: Export Markdown

Save to current working directory:
```
{podcast-title}-知识点整理.md
{podcast-title}-MiMo转录.md
```

## Token Estimation

Audio token consumption: `total_tokens ≈ audio_duration_seconds × 6.25`

For a 1h25m podcast (~5100s):
- Prompt tokens: ~32,000 (audio input)
- Completion tokens: ~19,000 (full transcript)
- Total: ~51,000 tokens

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Hallucinated content | CDN URL not accessible from cloud | Use RSS-authorized URL with `jt=` |
| `finish_reason: length` | Token limit hit | Increase `max_completion_tokens` |
| 401 Invalid API Key | Wrong endpoint | Use `https://token-plan-cn.xiaomimimo.com/v1` |
| Empty response | Audio format unsupported | Ensure URL points to .m4a file |
