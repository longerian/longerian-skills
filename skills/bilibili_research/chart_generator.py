"""
Chart generation module for data visualization.
Uses matplotlib to generate static PNG charts for reports.
"""

import os
import html
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Configure Chinese font support
def _setup_chinese_font():
    """Setup matplotlib to display Chinese characters correctly."""
    # Try common Chinese fonts
    font_paths = [
        '/System/Library/Fonts/PingFang.ttc',  # macOS
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux
        'C:/Windows/Fonts/msyh.ttc',  # Windows
        'C:/Windows/Fonts/simhei.ttf',  # Windows
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
            plt.rcParams['axes.unicode_minus'] = False
            return True

    # Fallback: use system default
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    return False

_setup_chinese_font()

# Import data structures from analyzer (now in same package)
# Try relative import first, fall back to absolute import
try:
    from .analyzer import DataPoint, ChartSpec
except ImportError:
    from analyzer import DataPoint, ChartSpec


# ============================================================================
# Chart Generation
# ============================================================================

@dataclass
class GeneratedChart:
    """Result of chart generation."""
    file_path: str           # Path to generated PNG file
    chart_type: str          # Type of chart generated
    title: str               # Chart title
    data_count: int          # Number of data points visualized


def generate_bar_chart(
    data_points: list[DataPoint],
    title: str,
    output_dir: str,
    filename: Optional[str] = None
) -> GeneratedChart:
    """
    Generate a bar chart from data points.

    Args:
        data_points: List of data points to visualize
        title: Chart title
        output_dir: Directory to save the chart
        filename: Output filename (default: auto-generated)

    Returns:
        GeneratedChart with file path and metadata
    """
    if not data_points:
        raise ValueError("No data points provided for bar chart")

    # Limit to top 15 items for readability
    sorted_data = sorted(data_points, key=lambda x: x.value, reverse=True)[:15]

    fig, ax = plt.subplots(figsize=(10, 6))

    labels = [dp.label[:20] + '...' if len(dp.label) > 20 else dp.label for dp in sorted_data]
    values = [dp.value for dp in sorted_data]
    units = sorted_data[0].unit if sorted_data else ""

    bars = ax.bar(range(len(labels)), values, color='#4A90E2', alpha=0.8)

    # Customize chart
    ax.set_xlabel('项目', fontsize=12)
    ax.set_ylabel(f'数值 ({units})' if units else '数值', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)

    # Add value labels on bars
    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    # Save chart
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"chart_bar_{len(data_points)}items.png"

    file_path = str(output_path / filename)
    plt.savefig(file_path, dpi=100, bbox_inches='tight')
    plt.close()

    return GeneratedChart(
        file_path=file_path,
        chart_type="bar",
        title=title,
        data_count=len(sorted_data)
    )


def generate_line_chart(
    data_points: list[DataPoint],
    title: str,
    output_dir: str,
    filename: Optional[str] = None
) -> GeneratedChart:
    """
    Generate a line chart from time-series data points.

    Args:
        data_points: List of data points to visualize
        title: Chart title
        output_dir: Directory to save the chart
        filename: Output filename (default: auto-generated)

    Returns:
        GeneratedChart with file path and metadata
    """
    if not data_points:
        raise ValueError("No data points provided for line chart")

    # Sort by timestamp if available
    sorted_data = sorted(data_points, key=lambda x: x.timestamp or 0)

    fig, ax = plt.subplots(figsize=(10, 6))

    labels = [dp.label[:15] + '...' if len(dp.label) > 15 else dp.label for dp in sorted_data]
    values = [dp.value for dp in sorted_data]

    ax.plot(range(len(labels)), values, marker='o', linewidth=2, markersize=8, color='#E94B3C')

    # Customize chart
    ax.set_xlabel('时间序列', fontsize=12)
    ax.set_ylabel(f'数值 ({sorted_data[0].unit})' if sorted_data and sorted_data[0].unit else '数值', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()

    # Save chart
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"chart_line_{len(data_points)}points.png"

    file_path = str(output_path / filename)
    plt.savefig(file_path, dpi=100, bbox_inches='tight')
    plt.close()

    return GeneratedChart(
        file_path=file_path,
        chart_type="line",
        title=title,
        data_count=len(sorted_data)
    )


def generate_comparison_table(
    data_points: list[DataPoint],
    title: str,
    output_dir: str,
    filename: Optional[str] = None
) -> GeneratedChart:
    """
    Generate a comparison table visualization from data points.

    Args:
        data_points: List of data points to visualize (best for 2-5 items)
        title: Chart title
        output_dir: Directory to save the chart
        filename: Output filename (default: auto-generated)

    Returns:
        GeneratedChart with file path and metadata
    """
    if not data_points:
        raise ValueError("No data points provided for comparison table")

    # Limit to 10 rows
    display_data = data_points[:10]

    fig, ax = plt.subplots(figsize=(10, 4))

    # Hide axes
    ax.axis('off')
    ax.axis('tight')

    # Build table data
    table_data = []
    for dp in display_data:
        value_str = f"{dp.value:.2f} {dp.unit}" if dp.unit else f"{dp.value:.2f}"
        table_data.append([dp.label, value_str, dp.category or '-', dp.context[:30] + '...' if len(dp.context) > 30 else dp.context])

    # Create table
    table = ax.table(
        cellText=table_data,
        colLabels=['项目', '数值', '分类', '说明'],
        cellLoc='left',
        loc='center',
        colWidths=[0.3, 0.15, 0.15, 0.4]
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)

    # Style header
    for i in range(4):
        table[(0, i)].set_facecolor('#4A90E2')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Style cells
    for i in range(1, len(table_data) + 1):
        for j in range(4):
            table[(i, j)].set_facecolor('#F5F5F5' if i % 2 == 0 else 'white')

    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()

    # Save chart
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"chart_table_{len(display_data)}items.png"

    file_path = str(output_path / filename)
    plt.savefig(file_path, dpi=100, bbox_inches='tight')
    plt.close()

    return GeneratedChart(
        file_path=file_path,
        chart_type="comparison_table",
        title=title,
        data_count=len(display_data)
    )


def generate_charts(
    chart_specs: list[ChartSpec],
    output_dir: str
) -> list[GeneratedChart]:
    """
    Generate multiple charts from chart specifications.

    Args:
        chart_specs: List of chart specifications
        output_dir: Directory to save charts

    Returns:
        List of GeneratedChart objects
    """
    charts = []

    for spec in chart_specs:
        try:
            if spec.chart_type == "bar":
                chart = generate_bar_chart(
                    spec.data_points,
                    spec.title,
                    output_dir
                )
            elif spec.chart_type == "line":
                chart = generate_line_chart(
                    spec.data_points,
                    spec.title,
                    output_dir
                )
            elif spec.chart_type == "comparison_table":
                chart = generate_comparison_table(
                    spec.data_points,
                    spec.title,
                    output_dir
                )
            else:
                # Default to bar chart
                chart = generate_bar_chart(
                    spec.data_points,
                    spec.title,
                    output_dir
                )

            charts.append(chart)

        except Exception as e:
            # Log error but continue generating other charts
            print(f"Warning: Failed to generate chart '{spec.title}': {e}")
            continue

    return charts


# ============================================================================
# Utility Functions
# ============================================================================

def chart_to_html(chart: GeneratedChart, base_dir: str = "") -> str:
    """
    Convert a generated chart to HTML embed code.

    Args:
        chart: GeneratedChart object
        base_dir: Base directory for relative path (default: absolute path)

    Returns:
        HTML string with embedded image
    """
    # Use relative path if base_dir provided
    if base_dir:
        try:
            rel_path = os.path.relpath(chart.file_path, base_dir)
        except ValueError:
            rel_path = chart.file_path
    else:
        rel_path = chart.file_path

    # Escape title for HTML safety (LLM-generated content)
    safe_title = html.escape(chart.title)

    return f'''
<div class="chart-container" style="margin: 20px 0;">
    <img src="{rel_path}" alt="{safe_title}" style="max-width: 100%; border: 1px solid #e0e0e0; border-radius: 4px;">
    <p style="text-align: center; font-size: 14px; color: #666; margin-top: 8px;">
        {safe_title} ({chart.data_count} 个数据点)
    </p>
</div>'''


def chart_to_markdown(chart: GeneratedChart, base_dir: str = "") -> str:
    """
    Convert a generated chart to Markdown embed code.

    Args:
        chart: GeneratedChart object
        base_dir: Base directory for relative path (default: absolute path)

    Returns:
        Markdown string with embedded image
    """
    # Use relative path if base_dir provided
    if base_dir:
        try:
            rel_path = os.path.relpath(chart.file_path, base_dir)
        except ValueError:
            rel_path = chart.file_path
    else:
        rel_path = chart.file_path

    return f'''
### {chart.title}

![{chart.title}]({rel_path})

*数据点数量: {chart.data_count}*
'''
