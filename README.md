# longerian-skills

Claude Code skills collection by longerian.

## Podcast Transcription Skills

Two engines available for podcast audio transcription:

- **Whisper** - local transcription using OpenAI Whisper large-v3-turbo
- **MiMo** - cloud transcription using MiniMax MiMo v2.5 API

Both provide complete pipeline: download audio → transcribe → organize knowledge → export Markdown.

## Installation

```bash
npx longerian-skills
```

This installs both skills to `~/.claude/skills/`.

## Usage

In Claude Code:

```
/podcast-transcribe-whisper https://www.xiaoyuzhoufm.com/episode/xxx
/podcast-transcribe-mimo https://www.xiaoyuzhoufm.com/episode/xxx
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MIMO_API_KEY` | For MiMo skill | MiniMax MiMo API key |

## Comparison

| Dimension | Whisper (local) | MiMo (cloud) |
|-----------|----------------|--------------|
| Punctuation | None | Complete |
| Segmentation | None | Natural paragraphs |
| Name accuracy | Errors common | Accurate |
| Speed | ~20min (CPU) | ~3min (API) |
| Cost | Free | Token-based |

## License

MIT
