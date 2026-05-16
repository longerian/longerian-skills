import os, sys, time, whisper
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

VIDEO_PATH = r"C:\Users\Administrator\.longerian\data\podcast\douyin_episode.mp4"
OUTPUT_DIR = r"C:\Users\Administrator\.longerian\data\douyin"
VIDEO_TITLE = "cpo光模块现在企稳了吗？英伟达和康宁联手定调！"
VIDEO_AUTHOR = "阿华（机构一手调研）"

print("Loading Whisper model...")
model = whisper.load_model('large-v3-turbo')

print("Transcribing...")
start = time.time()
result = model.transcribe(VIDEO_PATH, language='zh', verbose=False)
transcribe_time = time.time() - start

duration = result['segments'][-1]['end']
timestamp = int(time.time())
output_name = f"douyin_{timestamp}"

# Save plain text
transcript_path = os.path.join(OUTPUT_DIR, f'{output_name}-transcript.txt')
with open(transcript_path, 'w', encoding='utf-8') as f:
    f.write(result['text'])

# Generate Markdown report
md_path = os.path.join(OUTPUT_DIR, f'{output_name}-报告.md')
with open(md_path, 'w', encoding='utf-8') as f:
    # Header
    f.write(f"# {VIDEO_TITLE}\n\n")
    f.write(f"**作者**: {VIDEO_AUTHOR}\n")
    f.write(f"**转录时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"**视频时长**: {duration:.1f}秒 ({duration/60:.1f}分钟)\n")
    f.write(f"**转录耗时**: {transcribe_time:.1f}秒\n")
    f.write(f"**处理速度**: {duration/transcribe_time:.1f}x 实时\n\n")

    f.write("---\n\n")

    # Full transcript with punctuation
    f.write("## 完整转录\n\n")

    text = result['text']
    # Basic punctuation rules
    replacements = [
        ('哥几个', '哥几个，'),
        ('那么', '那么，'),
        ('但是', '但是，'),
        ('所以', '所以，'),
        ('因为', '因为，'),
        ('还有', '还有，'),
        ('另外', '另外，'),
        ('第一是', '第一是：'),
        ('第二个是', '第二个是：'),
        ('第三个是', '第三个是：'),
        ('老黄', '老黄（黄仁勋）'),
        ('老川', '老川（川普）'),
        ('库克', '库克（苹果CEO）'),
        ('老马', '老马（马斯克）'),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    f.write(text + "\n\n")

    # Segments with timestamps
    f.write("---\n\n## 分段转录 (带时间戳)\n\n")
    for i, seg in enumerate(result['segments'][:10], 1):  # First 10 segments
        minutes = int(seg['start'] // 60)
        seconds = int(seg['start'] % 60)
        f.write(f"### [{minutes}:{seconds:02d}] {seg['text']}\n\n")

    if len(result['segments']) > 10:
        f.write(f"\n_... 还有 {len(result['segments']) - 10} 个分段_\n")

print(f"\n✓ 转录完成!")
print(f"  文本: {transcript_path}")
print(f"  报告: {md_path}")
print(f"\n视频时长: {duration:.1f}秒")
print(f"转录耗时: {transcribe_time:.1f}秒")
print(f"处理速度: {duration/transcribe_time:.1f}x")
