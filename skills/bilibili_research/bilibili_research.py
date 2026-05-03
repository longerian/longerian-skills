#!/usr/bin/env python3
"""
Bilibili Video Research Assistant
Main entry point for extracting, analyzing, and reporting on Bilibili videos.
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.bilibili_research.extractor import extract, parse_bilibili_url
from shared.whisper_wrapper import transcribe
from shared.analyzer import analyze_content, AnalysisResult
from shared.report import generate_html_report, generate_markdown_report, open_report, ReportData


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
    parser = argparse.ArgumentParser(description='Bilibili Video Research Assistant')
    parser.add_argument('url', help='Bilibili video URL')
    parser.add_argument('--cookies', help='Path to cookies.txt for member videos')
    parser.add_argument('--no-fact-check', action='store_true', help='Skip fact-checking (faster)')
    parser.add_argument('--no-report', action='store_true', help='Skip HTML report generation')
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

    # Step 3: Analyze content
    print("🧠 正在分析内容...")
    try:
        analysis = analyze_content(
            transcript,
            title=result.title,
            metadata={
                'uploader': result.uploader,
                'duration': format_duration(result.duration),
                'url': url
            }
        )
        print(f"   ✅ 提取 {len(analysis.outline)} 个大纲要点")
        print(f"   ✅ 提取 {len(analysis.core_points)} 个核心观点")
        print(f"   ✅ 识别 {len(analysis.key_entities)} 个关键实体")
    except Exception as e:
        print(f"   ❌ 分析失败: {e}")
        return 1
    print()

    # Step 4: Fact check (optional)
    fact_checks = []
    if not args.no_fact_check and analysis.verifiable_claims:
        print("🔍 正在核查事实...")
        for i, claim in enumerate(analysis.verifiable_claims[:3], 1):  # Limit to 3 for speed
            print(f"   [{i}/{min(3, len(analysis.verifiable_claims))}] {claim[:50]}...")
            # TODO: Implement web search fact-checking
            # For now, create placeholder
            fact_checks.append({
                'claim': claim,
                'verified': False,
                'confidence': 0.0,
                'evidence': [],
                'summary': '事实核查功能待实现'
            })
        print()

    # Step 5: Generate report
    if not args.no_report:
        print("📄 正在生成报告...")
        report_data = ReportData(
            video_info={
                'title': result.title,
                'uploader': result.uploader,
                'duration_str': format_duration(result.duration),
                'url': url
            },
            analysis={
                'outline': analysis.outline,
                'core_points': analysis.core_points,
                'key_entities': analysis.key_entities,
                'verifiable_claims': analysis.verifiable_claims,
                'keywords': analysis.keywords,
                'summary': analysis.summary
            },
            fact_checks=fact_checks,
            related_reading=[],  # TODO: Implement extended reading
            generated_at='pending'  # Will fix immediately
        )

        # Fix generated_at
        from datetime import datetime
        report_data.generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Generate both HTML and Markdown reports
        html_path = generate_html_report(report_data)
        md_path = generate_markdown_report(report_data)
        print(f"   ✅ HTML 报告: {html_path}")
        print(f"   ✅ Markdown 报告: {md_path}")
        print()

        # Open HTML in browser
        print("🌐 正在打开浏览器...")
        open_report(html_path)

    # Summary
    print()
    print("=" * 50)
    print("📊 分析完成")
    print("=" * 50)
    print(f"📝 大纲: {len(analysis.outline)} 个要点")
    print(f"💡 核心观点: {len(analysis.core_points)} 条")
    print(f"🔍 事实核查: {len(fact_checks)} 条")
    print(f"📚 关键词: {len(analysis.keywords)} 个")
    if analysis.summary:
        print(f"\n📌 {analysis.summary}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
