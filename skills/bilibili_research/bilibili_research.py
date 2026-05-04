#!/usr/bin/env python3
"""
Bilibili Video Research Assistant
Extract subtitles/transcript from Bilibili videos for AI agent analysis.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.bilibili_research.extractor import extract, parse_bilibili_url
from shared.whisper_wrapper import transcribe


# Directory conventions
OUTPUT_DIR = Path.home() / '.longerian' / 'data' / 'bilibili-research'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def format_duration(seconds: int) -> str:
    """Format seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        m = seconds // 60
        s = seconds % 60
        return f"{m}分{s}秒"
    else:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}时{m}分"


def main():
    parser = argparse.ArgumentParser(description='Bilibili Video Research Assistant - Extract transcript for AI analysis')
    parser.add_argument('url', help='Bilibili video URL')
    parser.add_argument('--cookies', help='Path to cookies.txt for member videos')
    args = parser.parse_args()

    url = args.url

    # Validate URL
    video_id = parse_bilibili_url(url)
    if not video_id:
        print("❌ 无效的 Bilibili URL")
        return 1

    print(f"📺 正在处理视频: {video_id}")
    print()

    # Step 1: Extract content
    print("🔍 正在提取内容...")
    result = extract(url, str(OUTPUT_DIR), args.cookies)

    if result.error:
        print(f"❌ {result.error}")
        return 1

    print(f"   标题: {result.title}")
    print(f"   UP主: {result.uploader}")
    print(f"   时长: {format_duration(result.duration)}")
    print(f"   字幕: {'有' if result.has_subtitles else '无'}")

    # Get transcript
    transcript = result.transcript
    needs_transcription = False

    if not transcript and result.audio_path:
        needs_transcription = True
        estimated_time = result.duration / 60  # Rough estimate: 1 min audio per min processing on CPU
        print(f"   ⚠️  无字幕，需要转录音频（预计约 {estimated_time:.0f} 分钟）...")

    print()

    # Step 2: Transcribe if needed
    if needs_transcription:
        print("🎙️  正在转录音频...")
        try:
            transcription_result = transcribe(result.audio_path, verbose=True)
            transcript = transcription_result['text']
            print(f"   ✅ 转录完成，共 {len(transcript)} 字符")
        except Exception as e:
            print(f"   ❌ 转录失败: {e}")
            return 1
        print()

    # Step 3: Save transcript for AI agent analysis
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    transcript_file = OUTPUT_DIR / f'transcript_{video_id}_{timestamp}.txt'

    with open(transcript_file, 'w', encoding='utf-8') as f:
        f.write(f"# {result.title}\n\n")
        f.write(f"**视频信息**\n")
        f.write(f"- URL: {url}\n")
        f.write(f"- UP主: {result.uploader}\n")
        f.write(f"- 时长: {format_duration(result.duration)}\n")
        f.write(f"- 视频ID: {video_id}\n")
        f.write(f"\n**转录文本**\n\n")
        f.write(transcript)

    print(f"📝 转录已保存到: {transcript_file}")
    print(f"📏 转录文本: {len(transcript)} 字符")
    print()
    print(f"💡 下一步: 让 AI 分析此转录文件")
    print(f"   可使用 Read 工具读取: {transcript_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
