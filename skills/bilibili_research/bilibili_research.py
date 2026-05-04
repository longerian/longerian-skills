#!/usr/bin/env python3
"""
Bilibili Video Research Assistant
Main entry point for extracting, analyzing, and reporting on Bilibili videos.
Enhanced version with detailed content extraction and data visualization.
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.bilibili_research.extractor import extract, parse_bilibili_url
from shared.whisper_wrapper import transcribe
from shared.analyzer import analyze_content, EnhancedAnalysisResult
from shared.chart_generator import generate_charts
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


def analysis_to_dict(analysis: EnhancedAnalysisResult) -> dict:
    """Convert EnhancedAnalysisResult to dict for report generation."""
    return {
        'outline': analysis.outline,
        'core_points': analysis.core_points,
        'key_entities': analysis.key_entities,
        'verifiable_claims': analysis.verifiable_claims,
        'keywords': analysis.keywords,
        'summary': analysis.summary,
        'detailed_sections': [
            {
                'heading': ds.heading,
                'content': ds.content,
                'timestamps': ds.timestamps
            }
            for ds in analysis.detailed_sections
        ],
        'data_points': [
            {
                'label': dp.label,
                'value': dp.value,
                'unit': dp.unit,
                'category': dp.category,
                'context': dp.context,
                'timestamp': dp.timestamp
            }
            for dp in analysis.data_points
        ]
    }


def main():
    parser = argparse.ArgumentParser(description='Bilibili Video Research Assistant')
    parser.add_argument('url', help='Bilibili video URL')
    parser.add_argument('--cookies', help='Path to cookies.txt for member videos')
    parser.add_argument('--no-fact-check', action='store_true', help='Skip fact-checking (faster)')
    parser.add_argument('--no-report', action='store_true', help='Skip HTML report generation')
    parser.add_argument('--no-charts', action='store_true', help='Skip chart generation')
    parser.add_argument('--basic', action='store_true', help='Use basic analysis (no detailed content)')
    parser.add_argument('--model', default='glm-4-flash', help='LLM model to use (default: glm-4-flash)')
    parser.add_argument('--agent-analyze', action='store_true', help='Output transcript for AI agent analysis (skip LLM API call)')
    parser.add_argument('--skip-analysis', action='store_true', help='Skip analysis, only do transcription')
    parser.add_argument('--claude-analyze', action='store_true', help='Use Claude Agent for analysis (instead of GLM API)')
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

    # Step 3: Analyze content using Agent tool (if --use-agent flag)
    if hasattr(args, 'use_agent') and args.use_agent:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        transcript_file = OUTPUT_DIR / f'transcript_{video_id}_{timestamp}.txt'

        # Save transcript with metadata for agent analysis
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
        print(f"\n💡 请使用 Agent 工具分析此转录文件")
        print(f"   文件路径: {transcript_file}")
        return 0

    # Special mode: output for AI agent analysis (--agent-analyze flag)
    if args.agent_analyze or args.skip_analysis:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        transcript_file = OUTPUT_DIR / f'transcript_{video_id}_{timestamp}.txt'

        # Save transcript with metadata for agent analysis
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
        print(f"\n💡 下一步: 让 AI 分析此转录文件")
        print(f"   可使用 Read 工具读取: {transcript_file}")

        return 0 if args.skip_analysis else None  # Continue to analysis if not skip

    print("🧠 正在分析内容...")
    enhanced = not args.basic
    try:
        analysis = analyze_content(
            transcript,
            title=result.title,
            metadata={
                'uploader': result.uploader,
                'duration': format_duration(result.duration),
                'url': url
            },
            model=args.model,
            enhanced=enhanced,
            timeout=120
        )

        # Handle both AnalysisResult and EnhancedAnalysisResult
        if isinstance(analysis, EnhancedAnalysisResult):
            print(f"   ✅ 提取 {len(analysis.outline)} 个大纲要点")
            print(f"   ✅ 提取 {len(analysis.core_points)} 个核心观点")
            print(f"   ✅ 识别 {len(analysis.key_entities)} 个关键实体")
            print(f"   ✅ 生成 {len(analysis.detailed_sections)} 个详细章节")
            print(f"   ✅ 提取 {len(analysis.data_points)} 个数据点")
        else:
            print(f"   ✅ 提取 {len(analysis.outline)} 个大纲要点")
            print(f"   ✅ 提取 {len(analysis.core_points)} 个核心观点")
            print(f"   ✅ 识别 {len(analysis.key_entities)} 个关键实体")

    except Exception as e:
        print(f"   ❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()

    # Step 4: Generate charts (if enhanced and has data points)
    charts = []
    if enhanced and not args.no_charts and isinstance(analysis, EnhancedAnalysisResult):
        if analysis.chart_specs:
            print("📊 正在生成图表...")
            try:
                charts = generate_charts(analysis.chart_specs, str(OUTPUT_DIR))
                print(f"   ✅ 生成 {len(charts)} 个图表")
                for chart in charts:
                    print(f"      - {chart.title} ({chart.chart_type})")
            except Exception as e:
                print(f"   ⚠️  图表生成失败: {e}")
            print()

    # Step 5: Fact check (optional)
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

    # Step 6: Generate report
    if not args.no_report:
        print("📄 正在生成报告...")

        # Convert analysis to dict
        analysis_dict = analysis_to_dict(analysis) if isinstance(analysis, EnhancedAnalysisResult) else {
            'outline': analysis.outline,
            'core_points': analysis.core_points,
            'key_entities': analysis.key_entities,
            'verifiable_claims': analysis.verifiable_claims,
            'keywords': analysis.keywords,
            'summary': analysis.summary,
            'detailed_sections': [],
            'data_points': []
        }

        report_data = ReportData(
            video_info={
                'title': result.title,
                'uploader': result.uploader,
                'duration_str': format_duration(result.duration),
                'url': url
            },
            analysis=analysis_dict,
            fact_checks=fact_checks,
            related_reading=[],  # TODO: Implement extended reading
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            charts=charts
        )

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
    if isinstance(analysis, EnhancedAnalysisResult):
        print(f"📖 详细章节: {len(analysis.detailed_sections)} 个")
        print(f"📊 数据点: {len(analysis.data_points)} 个")
        print(f"📈 图表: {len(charts)} 个")
    if analysis.summary:
        print(f"\n📌 {analysis.summary}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
