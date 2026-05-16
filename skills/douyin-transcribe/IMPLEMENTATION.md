# Douyin Transcribe Implementation Details

This document contains the technical implementation details for the douyin-transcribe skill. See SKILL.md for usage.

## Pipeline Steps

### Step 1: Fetch Video URL with Playwright

```javascript
const { chromium } = require('playwright');

const browser = await chromium.launch();
const page = await browser.newPage();

let mediaUrl = null;

page.on('response', async (response) => {
  const url = response.url();
  if (url.includes('douyinvod.com') && url.includes('media-video')) {
    mediaUrl = url;  // Found the video URL
  }
});

await page.goto(douyinUrl);
await page.waitForTimeout(15000); // Wait for video to load
```

### Step 2: Download Video

```bash
curl -L -o ~/.longerian/data/douyin/video.mp4 "{VIDEO_URL}"
```

### Step 3: Transcribe with Whisper (GPU)

```python
import whisper

model = whisper.load_model('large-v3-turbo')  # Auto-detects GPU
result = model.transcribe('video.mp4', language='zh')
```

### Step 4: Enhanced Punctuation Rules

```javascript
// Conjunctions → add comma
text = text.replace(/(那么|但是|所以|因为)/g, '$1，');

// Ordinals → add colon
text = text.replace(/(第一是|其次|再其)/g, '$1：');

// Questions → add question mark
text = text.replace(/(吗|呢|吧).*(怎么|什么|为什么)/g, '？');

// Exclamations → add exclamation mark
text = text.replace(/(真的|确实|太).*(哎呀|哇)/g, '！');

// Name disambiguation
const names = {
  '老黄': '老黄（黄仁勋）',
  '老川': '老川（川普）',
  '库克': '库克（苹果CEO）',
  '老马': '老马（马斯克）',
  '雷总': '雷总（雷军）'
};
```

### Step 5: Keyword Extraction

```javascript
// High-frequency words (2-4 chars, frequency > 1)
const words = text.match(/[一-龥]{2,4}/g);
const freq = {};
words.forEach(w => freq[w] = (freq[w] || 0) + 1);
const highFreq = Object.entries(freq)
  .filter(([k, v]) => v > 1 && !stopwords.has(k))
  .sort((a, b) => b[1] - a[1])
  .slice(0, 10)
  .map(([k]) => k);

// Key phrases (English acronyms, industry terms)
const phrases = text.match(/[A-Z]{2,4}|[一-龥]{2,6}(技术|芯片|模块)/g) || [];
```

### Step 6: Generate Markdown Report

```javascript
const report = `# ${title}

**作者**: ${author}
**转录时间**: ${new Date().toLocaleString('zh-CN')}
**视频时长**: ${duration}秒 (${(duration/60).toFixed(1)}分钟)
**转录耗时**: ${transcribeTime}秒
**处理速度**: ${(duration/transcribeTime).toFixed(1)}x 实时

---

## 关键词

**高频词**: ${highFreq.join('、')}
**关键短语**: ${phrases.join('、')}

---

## 完整转录

${punctuatedText}

---

## 分段转录 (带时间戳)

${segments.map(s => `### [${formatTime(s.start)}] ${s.text}`).join('\n\n')}
`;
```

## Full Script Structure

```
douyin-transcribe/
├── SKILL.md              # User-facing documentation
├── IMPLEMENTATION.md     # This file - technical details
├── douyin_transcribe.js  # Main entry point
├── douyin_download_and_transcribe.js  # Combined script
├── douyin_transcribe.py  # Whisper wrapper
├── test_markdown.py      # Report format tester
└── README.md             # Quick start guide
```

## Troubleshooting

### CUDA Not Available

```bash
# Check Python version (must be 3.12)
python --version

# Reinstall PyTorch with CUDA
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Video URL Not Found

- Douyin URLs have expiring signatures
- Refresh the page and copy URL again
- Check internet connection
- Try different URL format

### Poor Transcription Quality

- Original video audio quality matters
- Background music/noise affects accuracy
- Consider using larger model: `large-v3-turbo` is recommended for Chinese
- For English content, other models may work better

### Playwright Issues

```bash
# Reinstall browsers
npx playwright install
```

## Model Comparison

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| base | 74MB | Fastest | Lower |
| small | 244MB | Fast | Medium |
| medium | 769MB | Medium | Good |
| large-v3-turbo | 1.5GB | Fast | Best |
| large-v3 | 3.0GB | Slowest | Best |

**Recommendation**: `large-v3-turbo` for Chinese - best accuracy with good speed.
