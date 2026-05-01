# longerian-skills

Agent skills collection by longerian. Compatible with Claude Code, OpenClaw, Qoder, and other agents.

## Skills

| Skill | Description |
|-------|-------------|
| [podcast-transcribe-whisper](skills/podcast-transcribe-whisper/SKILL.md) | Local podcast transcription using Whisper large-v3-turbo |
| [podcast-transcribe-mimo](skills/podcast-transcribe-mimo/SKILL.md) | Cloud podcast transcription using MiniMax MiMo v2.5 API |
| [dii-estimator](skills/dii-estimator/SKILL.md) | Estimate Dietary Inflammatory Index (DII) from food photos |
| [option-yield](skills/option-yield/SKILL.md) | Calculate annualized premium yield for sold options (puts/calls) |

## Installation

Install all skills:

```bash
npx skills add longerian/longerian-skills
```

Install specific skill:

```bash
npx skills add longerian/longerian-skills --skill podcast-transcribe-mimo
```

The installer will auto-detect your installed agents and let you choose where to install.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MIMO_API_KEY` | For MiMo skill | MiniMax MiMo API key |

## Whisper vs MiMo

| Dimension | Whisper (local) | MiMo (cloud) |
|-----------|----------------|--------------|
| Punctuation | None | Complete |
| Segmentation | None | Natural paragraphs |
| Name accuracy | Errors common | Accurate |
| Speed | ~20min (CPU) | ~3min (API) |
| Cost | Free | Token-based |

## License

MIT
