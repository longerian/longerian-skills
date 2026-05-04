"""
Shared report generation module.
Generates HTML and Markdown reports with embedded charts.
"""

import os
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, asdict


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class FactCheckResult:
    """Result of fact verification."""
    claim: str
    verified: bool
    confidence: float
    evidence: list[str]
    summary: str


@dataclass
class RelatedReading:
    """Extended reading material."""
    title: str
    url: str
    source: str
    relevance_score: float


@dataclass
class GeneratedChart:
    """Result of chart generation."""
    file_path: str
    chart_type: str
    title: str
    data_count: int


@dataclass
class DetailedSection:
    """A detailed section with full content."""
    heading: str
    content: str
    timestamps: list[int] = None

    def __post_init__(self):
        if self.timestamps is None:
            self.timestamps = []


@dataclass
class ReportData:
    """Complete report data."""
    video_info: dict
    analysis: dict
    fact_checks: list[dict] = None
    related_reading: list[dict] = None
    generated_at: str = None
    charts: list[GeneratedChart] = None

    def __post_init__(self):
        if self.fact_checks is None:
            self.fact_checks = []
        if self.related_reading is None:
            self.related_reading = []
        if self.charts is None:
            self.charts = []


# ============================================================================
# HTML Report Generation
# ============================================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 研究报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 40px auto; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 28px; margin-bottom: 8px; color: #111; }}
        .meta {{ color: #666; font-size: 14px; margin-bottom: 30px; }}
        .meta a {{ color: #0066cc; text-decoration: none; }}
        .meta a:hover {{ text-decoration: underline; }}
        h2 {{ font-size: 20px; margin: 30px 0 15px; padding-bottom: 8px; border-bottom: 2px solid #0066cc; color: #222; }}
        h3 {{ font-size: 16px; margin: 20px 0 10px; color: #444; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
        .summary {{ background: #f0f7ff; padding: 20px; border-radius: 6px; border-left: 4px solid #0066cc; margin: 20px 0; font-size: 16px; }}
        .detailed-section {{ margin: 25px 0; padding: 20px; background: #fafafa; border-radius: 6px; border-left: 3px solid #ddd; }}
        .detailed-section h4 {{ color: #333; margin-bottom: 12px; font-size: 15px; }}
        .detailed-section p {{ margin-bottom: 10px; line-height: 1.8; text-align: justify; }}
        .claim {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .claim.verified {{ border-left: 4px solid #28a745; }}
        .claim.unverified {{ border-left: 4px solid #dc3545; }}
        .claim-header {{ font-weight: 600; margin-bottom: 5px; }}
        .claim-evidence {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .reading {{ background: #fff; padding: 12px; margin: 8px 0; border: 1px solid #e0e0e0; border-radius: 4px; }}
        .reading a {{ color: #0066cc; text-decoration: none; font-weight: 500; }}
        .reading a:hover {{ text-decoration: underline; }}
        .reading .source {{ font-size: 12px; color: #888; margin-top: 4px; }}
        .chart-container {{ margin: 25px 0; text-align: center; }}
        .chart-container img {{ max-width: 100%; border: 1px solid #e0e0e0; border-radius: 4px; }}
        .chart-caption {{ font-size: 13px; color: #666; margin-top: 8px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta">
            {uploader} · {duration} · <a href="{url}" target="_blank">查看原视频</a>
        </div>

        {summary_section}

        <h2>内容大纲</h2>
        <ul>
            {outline_items}
        </ul>

        {detailed_sections}

        <h2>核心观点</h2>
        <ul>
            {core_points}
        </ul>

        <h2>关键实体</h2>
        <p>{key_entities}</p>

        {charts_section}

        {fact_check_section}

        {reading_section}

        <div class="footer">
            生成时间: {generated_at}
        </div>
    </div>
</body>
</html>"""


def _render_detailed_sections_html(sections: list) -> str:
    """Render detailed sections as HTML."""
    if not sections:
        return ""

    html = ['<h2>详细内容</h2>']

    for section in sections:
        heading = section.get('heading', '')
        content = section.get('content', '')

        # Split content by double newlines into paragraphs
        paragraphs = content.split('\n\n')

        html.append(f'''
        <div class="detailed-section">
            <h4>{heading}</h4>''')

        for para in paragraphs:
            para = para.strip()
            if para:
                html.append(f'<p>{para}</p>')

        html.append('</div>')

    return '\n'.join(html)


def _render_charts_html(charts: list, output_dir: str) -> str:
    """Render charts as HTML."""
    if not charts:
        return ""

    html = ['<h2>数据可视化</h2>']

    for chart in charts:
        # Use relative path from output directory
        try:
            rel_path = os.path.relpath(chart.file_path, output_dir)
        except ValueError:
            rel_path = chart.file_path

        html.append(f'''
        <div class="chart-container">
            <img src="{rel_path}" alt="{chart.title}">
            <p class="chart-caption">{chart.title} ({chart.data_count} 个数据点)</p>
        </div>''')

    return '\n'.join(html)


def generate_html_report(
    data: ReportData,
    output_path: Optional[str] = None
) -> str:
    """
    Generate HTML report from analysis data.

    Args:
        data: ReportData with all analysis results
        output_path: Where to save HTML (default: auto-generated)

    Returns:
        Path to generated HTML file
    """
    if output_path is None:
        output_dir = Path.home() / '.longerian' / 'data' / 'bilibili-research'
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = str(output_dir / f'report_{timestamp}.html')

    output_dir = str(Path(output_path).parent)

    # Build outline items
    outline_items = '\n            '.join(
        f'<li>{item}</li>' for item in data.analysis.get('outline', [])
    )

    # Build core points
    core_points = '\n            '.join(
        f'<li>{p}</li>' for p in data.analysis.get('core_points', [])
    )

    # Build key entities
    key_entities = ' · '.join(data.analysis.get('key_entities', []))

    # Build summary section
    summary = data.analysis.get('summary', '')
    summary_section = f'<div class="summary">{summary}</div>' if summary else ''

    # Build detailed sections
    detailed_sections = _render_detailed_sections_html(
        data.analysis.get('detailed_sections', [])
    )

    # Build charts section
    charts_section = _render_charts_html(data.charts or [], output_dir)

    # Build fact-check section
    fact_check_html = ''
    if data.fact_checks:
        fc_items = []
        for fc in data.fact_checks:
            status_class = 'verified' if fc.get('verified') else 'unverified'
            evidence = '<br>'.join(f'  · {e}' for e in fc.get('evidence', []))
            fc_items.append(f'''
            <div class="claim {status_class}">
                <div class="claim-header">{fc.get('claim', '')}</div>
                <div>{fc.get('summary', '')}</div>
                <div class="claim-evidence">{evidence}</div>
            </div>''')
        fact_check_html = f'<h2>事实核查</h2>\n' + '\n'.join(fc_items)

    # Build reading section
    reading_html = ''
    if data.related_reading:
        reading_items = []
        for r in data.related_reading:
            reading_items.append(f'''
            <div class="reading">
                <a href="{r.get('url', '')}" target="_blank">{r.get('title', '')}</a>
                <div class="source">{r.get('source', '')}</div>
            </div>''')
        reading_html = '<h2>扩展阅读</h2>\n' + '\n'.join(reading_items)

    # Render template
    html = HTML_TEMPLATE.format(
        title=data.video_info.get('title', 'Unknown'),
        uploader=data.video_info.get('uploader', ''),
        duration=data.video_info.get('duration_str', ''),
        url=data.video_info.get('url', ''),
        summary_section=summary_section,
        outline_items=outline_items,
        detailed_sections=detailed_sections,
        core_points=core_points,
        key_entities=key_entities,
        charts_section=charts_section,
        fact_check_section=fact_check_html,
        reading_section=reading_html,
        generated_at=data.generated_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    # Write file
    Path(output_path).write_text(html, encoding='utf-8')

    return output_path


# ============================================================================
# Markdown Report Generation
# ============================================================================

def generate_markdown_report(
    data: ReportData,
    output_path: Optional[str] = None
) -> str:
    """
    Generate Markdown report from analysis data.

    Args:
        data: ReportData with all analysis results
        output_path: Where to save Markdown (default: auto-generated)

    Returns:
        Path to generated Markdown file
    """
    if output_path is None:
        output_dir = Path.home() / '.longerian' / 'data' / 'bilibili-research'
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = str(output_dir / f'report_{timestamp}.md')

    output_dir = str(Path(output_path).parent)
    lines = []

    # Header
    title = data.video_info.get('title', 'Unknown')
    lines.append(f'# {title}\n')
    lines.append(f'**UP主:** {data.video_info.get("uploader", "")}')
    lines.append(f'**时长:** {data.video_info.get("duration_str", "")}')
    lines.append(f'**链接:** {data.video_info.get("url", "")}\n')

    # Summary
    summary = data.analysis.get('summary', '')
    if summary:
        lines.append(f'## 📌 总结\n\n{summary}\n')

    # Outline
    outline = data.analysis.get('outline', [])
    if outline:
        lines.append('## 📋 内容大纲\n')
        for i, item in enumerate(outline, 1):
            lines.append(f'{i}. {item}')
        lines.append('')

    # Detailed sections
    detailed_sections = data.analysis.get('detailed_sections', [])
    if detailed_sections:
        lines.append('## 📖 详细内容\n')
        for section in detailed_sections:
            heading = section.get('heading', '')
            content = section.get('content', '')
            lines.append(f'### {heading}\n')
            lines.append(content)
            lines.append('')

    # Core points
    core_points = data.analysis.get('core_points', [])
    if core_points:
        lines.append('## 💡 核心观点\n')
        for i, point in enumerate(core_points, 1):
            lines.append(f'{i}. {point}')
        lines.append('')

    # Key entities
    entities = data.analysis.get('key_entities', [])
    if entities:
        lines.append('## 🏷️ 关键实体\n\n')
        lines.append(' · '.join(entities) + '\n')

    # Charts
    charts = data.charts or []
    if charts:
        lines.append('## 📊 数据可视化\n')
        for chart in charts:
            try:
                rel_path = os.path.relpath(chart.file_path, output_dir)
            except ValueError:
                rel_path = chart.file_path

            lines.append(f'### {chart.title}\n')
            lines.append(f'![{chart.title}]({rel_path})\n')
            lines.append(f'*数据点数量: {chart.data_count}*\n')
        lines.append('')

    # Fact checks
    if data.fact_checks:
        lines.append('## 🔍 事实核查\n')
        for fc in data.fact_checks:
            status = '✅ 验证通过' if fc.get('verified') else '❌ 未验证'
            lines.append(f'- **{fc.get("claim", "")}** ({status})')
            if fc.get('summary'):
                lines.append(f'  - {fc.get("summary")}')
            for ev in fc.get('evidence', []):
                lines.append(f'  - 证据: {ev}')
            lines.append('')

    # Related reading
    if data.related_reading:
        lines.append('## 📚 扩展阅读\n')
        for r in data.related_reading:
            lines.append(f'- [{r.get("title", "")}]({r.get("url", "")})')
            lines.append(f'  - 来源: {r.get("source", "")}')
        lines.append('')

    # Footer
    lines.append(f'---\n\n*生成时间: {data.generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*')

    # Write file
    markdown = '\n'.join(lines)
    Path(output_path).write_text(markdown, encoding='utf-8')

    return output_path


# ============================================================================
# Utility Functions
# ============================================================================

def open_report(html_path: str) -> None:
    """Open HTML report in default browser."""
    webbrowser.open(f'file://{html_path}')
