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
    """Generate the analysis prompt for AI Agent."""
    return f"""请详细分析以下视频转录内容，提取实质性知识点（不要说"视频介绍了"这类元描述）：

# {title}
- UP主: {uploader}
- 时长: {duration}

{transcript}

请按以下结构输出分析报告：

## 一、核心主题
简要概述视频的核心主题（2-3句话）

## 二、关键信息点
提取视频中的关键信息点，每点用具体数据支撑：
- 信息点1（含具体数据）
- 信息点2（含具体数据）
- ...

## 三、技术/概念详解
对视频中的技术概念或专业术语进行详细解释：
1. 概念名称：具体说明
2. 概念名称：具体说明
...

## 四、数据汇总
用表格形式汇总视频中提到的关键数据：

| 指标 | 数值 | 单位 | 说明 |
|------|------|------|------|
| ... | ... | ... | ... |

## 五、对比分析
如果视频涉及对比分析，请整理成表格：

| 项目 | 方案A | 方案B | 说明 |
|------|-------|-------|------|
| ... | ... | ... | ... |

## 六、风险与机会
- **机会**：列出1-3点
- **风险**：列出1-3点

## 七、结论
总结视频的核心结论（2-3句话）

请直接输出实质性内容，用第三人称客观陈述。"""


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


def main():
    parser = argparse.ArgumentParser(
        description='Bilibili Video Research Assistant - Extract and analyze video content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  (default)     Agent mode - Extract transcript for AI Agent analysis
  --report       Report mode - Generate full HTML/Markdown report with charts
  --prompt-only  Prompt mode - Only generate analysis prompt template

Examples:
  python bilibili_research.py "https://www.bilibili.com/video/BV..."
  python bilibili_research.py "https://www.bilibili.com/video/BV..." --report
  python bilibili_research.py "https://www.bilibili.com/video/BV..." --prompt-only
        """
    )
    parser.add_argument('url', help='Bilibili video URL')
    parser.add_argument('--cookies', help='Path to cookies.txt for member videos')
    parser.add_argument('--skip-report', action='store_true', help='Skip report generation, only save transcript')
    parser.add_argument('--report', action='store_true', help='Generate full HTML/Markdown report with charts')
    parser.add_argument('--prompt-only', action='store_true', help='Only generate analysis prompt template')
    parser.add_argument('--no-charts', action='store_true', help='Skip chart generation in report mode')
    parser.add_argument('--basic', action='store_true', help='Use basic analysis (no detailed content)')
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

    if args.skip_report:
        print("💡 跳过报告生成（使用 --skip-report 选项）")
        return 0

    # Report mode: Generate full report with LLM analysis
    if args.report:
        return generate_full_report(
            result, transcript, url, video_id, timestamp, args
        )

    # Prompt-only mode: Only generate prompt template
    if args.prompt_only:
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
        print(f"   请 AI 读取并分析: {analysis_prompt_file}")
        return 0

    # Default: Agent mode with next steps
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
    print("💡 下一步: 让 AI Agent 分析此视频")
    print("=" * 60)
    print()
    print("方案 A - 直接让 AI 读取分析提示文件:")
    print(f"   请 AI 读取并分析: {analysis_prompt_file}")
    print()
    print("方案 B - AI 读取转录文件后使用提示模板:")
    print(f"   1. 读取转录: {transcript_file}")
    print("   2. 使用结构化分析提示（见 SKILL.md）")
    print()
    print("方案 C - 生成完整报告:")
    print(f"   python bilibili_research.py {url} --report")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
