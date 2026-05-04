#!/usr/bin/env python3
"""
Bilibili Video Research Assistant
Extract subtitles/transcript from Bilibili videos and generate research reports.

Three modes:
1. Agent mode (default): Extract transcript for AI Agent analysis
2. Report mode: Generate full HTML/Markdown report with charts (requires LLM API)
3. Prompt mode: Generate analysis prompt template for AI Agent
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Handle both direct execution and module import
# When installed, the script is in .claude/skills/bilibili-research/
# When developing, the script is in skills/bilibili_research/
current_dir = Path(__file__).parent
if (current_dir.parent.name == 'skills' and current_dir.parent.parent.name == '.claude'):
    # Installed environment: .claude/skills/bilibili-research/
    # Add project root to sys.path for shared modules if available
    project_root = current_dir.parent.parent.parent
    if (project_root / 'shared').exists():
        sys.path.insert(0, str(project_root))
elif current_dir.parent.name == 'skills':
    # Development environment: skills/bilibili_research/
    # Add project root to sys.path
    sys.path.insert(0, str(current_dir.parent.parent))

# Try relative import first (works when run as module)
try:
    from .extractor import extract, parse_bilibili_url
    from .whisper_wrapper import transcribe
    # Report modules (optional - only used in report mode)
    from . import analyzer, chart_generator, report
except ImportError:
    # Fall back to absolute import (works when script is run directly)
    from extractor import extract, parse_bilibili_url
    from whisper_wrapper import transcribe
    # Report modules (optional)
    import analyzer, chart_generator, report


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


def generate_analysis_prompt(title: str, uploader: str, duration: str, transcript: str) -> str:
    """Generate the adaptive analysis prompt for AI Agent.

    The prompt is designed to let AI identify content type and generate
    appropriate report structure automatically, not using a fixed template.
    """
    return f"""请详细分析以下视频转录内容。

**任务：识别内容类型并生成适配的分析报告**

首先判断视频的内容类型（公司分析、技术教程、评论观点、新闻资讯、访谈对话、其他等），然后根据类型生成适配的报告结构。

不要使用固定的"技术/概念详解"、"数据汇总"、"对比分析"等模板章节。让 AI 根据内容特点自行决定报告的结构和章节标题。

例如：
- 公司分析：公司概况、财务表现、产品技术、竞争格局、发展前景
- 技术教程：背景介绍、核心概念、实现步骤、注意事项、延伸阅读
- 评论观点：事件背景、各方观点、分析论证、结论判断
- 新闻资讯：事件要素、时间线、相关方、影响分析

**要求：**
1. 提取实质性知识点，不要说"视频介绍了"这类元描述
2. 用第三人称客观陈述
3. 根据内容类型自适应报告结构

---
# {title}
- UP主: {uploader}
- 时长: {duration}

{transcript}

请根据内容类型生成适配的分析报告。"""


def generate_full_report(result, transcript: str, url: str, video_id: str, timestamp: str, args) -> int:
    """Generate full HTML/Markdown report with charts and LLM analysis."""
    import os

    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('ZHIPU_API_KEY')
    if not api_key:
        print("❌ 报告模式需要 LLM API")
        print("   请设置环境变量: OPENAI_API_KEY 或 ZHIPU_API_KEY")
        print()
        print("💡 使用提示模式代替:")
        print(f"   python bilibili_research.py {url} --prompt-only")
        return 1

    # Step 1: Analyze content with LLM
    print("🧠 正在分析内容...")
    enhanced = not args.basic
    try:
        analysis_result = analyzer.analyze_content(
            transcript,
            title=result.title,
            metadata={
                'uploader': result.uploader,
                'duration': format_duration(result.duration),
                'url': url
            },
            model=args.model,
            enhanced=enhanced,
            timeout=300
        )

        if isinstance(analysis_result, analyzer.EnhancedAnalysisResult):
            print(f"   ✅ 提取 {len(analysis_result.outline)} 个大纲要点")
            print(f"   ✅ 提取 {len(analysis_result.core_points)} 个核心观点")
            print(f"   ✅ 识别 {len(analysis_result.key_entities)} 个关键实体")
            print(f"   ✅ 生成 {len(analysis_result.detailed_sections)} 个详细章节")
            print(f"   ✅ 提取 {len(analysis_result.data_points)} 个数据点")
        else:
            print(f"   ✅ 提取 {len(analysis_result.outline)} 个大纲要点")
            print(f"   ✅ 提取 {len(analysis_result.core_points)} 个核心观点")
            print(f"   ✅ 识别 {len(analysis_result.key_entities)} 个关键实体")

    except Exception as e:
        print(f"   ❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    print()

    # Step 2: Generate charts (if enhanced and has data points)
    generated_charts = []
    if enhanced and not args.no_charts and isinstance(analysis_result, analyzer.EnhancedAnalysisResult):
        if analysis_result.chart_specs:
            print("📊 正在生成图表...")
            try:
                generated_charts = chart_generator.generate_charts(
                    analysis_result.chart_specs, str(OUTPUT_DIR)
                )
                print(f"   ✅ 生成 {len(generated_charts)} 个图表")
                for chart in generated_charts:
                    print(f"      - {chart.title} ({chart.chart_type})")
            except Exception as e:
                print(f"   ⚠️  图表生成失败: {e}")
            print()

    # Step 3: Prepare report data
    report_data = report.ReportData(
        video_id=video_id,
        url=url,
        title=result.title,
        uploader=result.uploader,
        duration=format_duration(result.duration),
        transcript=transcript,
        outline=analysis_result.outline,
        core_points=analysis_result.core_points,
        key_entities=analysis_result.key_entities,
        verifiable_claims=analysis_result.verifiable_claims if hasattr(analysis_result, 'verifiable_claims') else [],
        keywords=analysis_result.keywords if hasattr(analysis_result, 'keywords') else [],
        summary=analysis_result.summary if hasattr(analysis_result, 'summary') else '',
        detailed_sections=[],
        data_points=[],
        charts=generated_charts,
        fact_checks=[],
        related_reading=[],
        generated_at=datetime.now()
    )

    if isinstance(analysis_result, analyzer.EnhancedAnalysisResult):
        report_data.detailed_sections = [
            report.DetailedSection(
                heading=ds.heading,
                content=ds.content,
                timestamps=ds.timestamps
            )
            for ds in analysis_result.detailed_sections
        ]
        report_data.data_points = [
            report.DataPoint(
                label=dp.label,
                value=dp.value,
                unit=dp.unit,
                category=dp.category,
                context=dp.context,
                timestamp=dp.timestamp
            )
            for dp in analysis_result.data_points
        ]

    # Step 4: Generate Markdown report
    print("📄 正在生成 Markdown 报告...")
    md_file = OUTPUT_DIR / f'report_{video_id}_{timestamp}.md'
    try:
        report.generate_markdown_report(report_data, str(md_file))
        print(f"   ✅ Markdown 报告: {md_file}")
    except Exception as e:
        print(f"   ⚠️  Markdown 生成失败: {e}")

    # Step 5: Generate HTML report
    print("🌐 正在生成 HTML 报告...")
    html_file = OUTPUT_DIR / f'report_{video_id}_{timestamp}.html'
    try:
        report.generate_html_report(report_data, str(html_file))
        print(f"   ✅ HTML 报告: {html_file}")
    except Exception as e:
        print(f"   ⚠️  HTML 生成失败: {e}")

    print()
    print("=" * 60)
    print("✅ 报告生成完成")
    print("=" * 60)
    print()

    # Open in browser if requested
    if args.open:
        print("正在打开浏览器...")
        report.open_report(str(html_file))

    return 0


def generate_agent_mode_output(result, transcript: str, url: str, video_id: str, timestamp: str) -> int:
    """Generate transcript and prompt for AI Agent analysis."""
    # Save transcript
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

    # Generate analysis prompt
    analysis_prompt_file = OUTPUT_DIR / f'prompt_{video_id}_{timestamp}.txt'
    prompt = generate_analysis_prompt(
        title=result.title,
        uploader=result.uploader,
        duration=format_duration(result.duration),
        transcript=transcript
    )

    with open(analysis_prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"📋 分析提示已保存到: {analysis_prompt_file}")
    print()
    print("=" * 60)
    print("💡 让 AI Agent 分析此视频")
    print("=" * 60)
    print()
    print("请 AI 读取并分析:")
    print(f"   {analysis_prompt_file}")
    print()

    return 0


def generate_prompt_only(result, transcript: str, url: str, video_id: str, timestamp: str) -> int:
    """Generate only the analysis prompt template."""
    analysis_prompt_file = OUTPUT_DIR / f'prompt_{video_id}_{timestamp}.txt'
    prompt = generate_analysis_prompt(
        title=result.title,
        uploader=result.uploader,
        duration=format_duration(result.duration),
        transcript=transcript
    )

    with open(analysis_prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"📋 分析提示已保存到: {analysis_prompt_file}")
    print()
    print("💡 让 AI Agent 分析此视频:")
    print(f"   请 AI 读取: {analysis_prompt_file}")
    print()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Bilibili Video Research Assistant - Extract and analyze video content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  (default)     Report mode - Generate full HTML/Markdown report with charts
  --agent-mode   Agent mode - Extract transcript for AI Agent analysis
  --prompt-only  Prompt mode - Only generate analysis prompt template

Examples:
  python bilibili_research.py "https://www.bilibili.com/video/BV..."
  python bilibili_research.py "https://www.bilibili.com/video/BV..." --agent-mode
  python bilibili_research.py "https://www.bilibili.com/video/BV..." --prompt-only
        """
    )
    parser.add_argument('url', help='Bilibili video URL')
    parser.add_argument('--cookies', help='Path to cookies.txt for member videos')
    parser.add_argument('--agent-mode', action='store_true', help='Agent mode: extract transcript for AI Agent analysis (default is report mode)')
    parser.add_argument('--prompt-only', action='store_true', help='Prompt mode: only generate analysis prompt template')
    parser.add_argument('--no-charts', action='store_true', help='Skip chart generation in report mode')
    parser.add_argument('--basic', action='store_true', help='Use basic analysis (faster, no detailed content)')
    parser.add_argument('--model', default='glm-4-flash', help='LLM model for report generation (default: glm-4-flash)')
    parser.add_argument('--open', action='store_true', help='Open HTML report in browser after generation')
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

    # Step 3: Save transcript
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

    # Agent mode: Extract transcript for AI Agent (explicit opt-in)
    if args.agent_mode:
        return generate_agent_mode_output(
            result, transcript, url, video_id, timestamp
        )

    # Prompt-only mode: Only generate prompt template
    if args.prompt_only:
        return generate_prompt_only(
            result, transcript, url, video_id, timestamp
        )

    # Default: Report mode - Generate full HTML/Markdown report with LLM analysis
    return generate_full_report(
        result, transcript, url, video_id, timestamp, args
    )


if __name__ == '__main__':
    sys.exit(main())
