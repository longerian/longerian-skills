"""
Tests for shared.report module.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from shared.report import (
    FactCheckResult,
    RelatedReading,
    GeneratedChart,
    DetailedSection,
    ReportData,
    generate_html_report,
    generate_markdown_report,
    open_report,
    _render_detailed_sections_html,
    _render_charts_html
)


# ============================================================================
# HTML Report Generation Tests
# ============================================================================

class TestGenerateHtmlReport:
    """Tests for generate_html_report function."""

    def test_generate_html_creates_file(self, tmp_path, sample_report_data):
        """Test HTML report generation creates a file."""
        output_path = tmp_path / 'test_report.html'

        result = generate_html_report(sample_report_data, str(output_path))

        assert Path(result).exists()
        assert Path(result).suffix == '.html'

    def test_html_contains_basic_sections(self, tmp_path, sample_report_data):
        """Test HTML report contains all basic sections."""
        output_path = tmp_path / 'test.html'
        result_path = generate_html_report(sample_report_data, str(output_path))

        content = Path(result_path).read_text(encoding='utf-8')

        assert '英伟达H100 GPU深度解析' in content  # title
        assert 'TechChannel' in content  # uploader
        assert '内容大纲' in content
        assert '核心观点' in content
        assert '关键实体' in content

    def test_html_contains_detailed_sections(self, tmp_path, sample_report_data):
        """Test HTML report contains detailed sections."""
        output_path = tmp_path / 'test.html'
        result_path = generate_html_report(sample_report_data, str(output_path))

        content = Path(result_path).read_text(encoding='utf-8')

        assert '详细内容' in content
        assert '英伟达H100 GPU规格介绍' in content
        assert 'HBM3内存' in content

    def test_html_contains_charts(self, tmp_path, sample_report_data):
        """Test HTML report includes chart references."""
        # Add a chart to the report data
        chart = GeneratedChart(
            file_path=str(tmp_path / 'test_chart.png'),
            chart_type='bar',
            title='Test Chart',
            data_count=5
        )
        # Create the chart file
        Path(chart.file_path).write_text('fake image')

        sample_report_data.charts = [chart]

        output_path = tmp_path / 'test.html'
        result_path = generate_html_report(sample_report_data, str(output_path))

        content = Path(result_path).read_text(encoding='utf-8')

        assert '数据可视化' in content
        assert 'Test Chart' in content
        assert '5 个数据点' in content

    def test_html_generates_default_path_when_not_specified(self, sample_report_data):
        """Test generates default output path when not specified."""
        result = generate_html_report(sample_report_data)

        assert Path(result).parent.exists()
        assert 'report_' in result
        assert result.endswith('.html')

    def test_html_contains_fact_checks(self, tmp_path, sample_report_data):
        """Test HTML report includes fact check results."""
        sample_report_data.fact_checks = [
            {
                'claim': 'Test claim',
                'verified': True,
                'confidence': 0.9,
                'evidence': ['Evidence 1', 'Evidence 2'],
                'summary': 'Verified'
            }
        ]

        output_path = tmp_path / 'test.html'
        result_path = generate_html_report(sample_report_data, str(output_path))

        content = Path(result_path).read_text(encoding='utf-8')

        assert '事实核查' in content
        assert 'Test claim' in content
        assert 'verified' in content


# ============================================================================
# Markdown Report Generation Tests
# ============================================================================

class TestGenerateMarkdownReport:
    """Tests for generate_markdown_report function."""

    def test_generate_markdown_creates_file(self, tmp_path, sample_report_data):
        """Test Markdown report generation creates a file."""
        output_path = tmp_path / 'test_report.md'

        result = generate_markdown_report(sample_report_data, str(output_path))

        assert Path(result).exists()
        assert Path(result).suffix == '.md'

    def test_markdown_contains_basic_sections(self, tmp_path, sample_report_data):
        """Test Markdown report contains all basic sections."""
        output_path = tmp_path / 'test.md'
        result_path = generate_markdown_report(sample_report_data, str(output_path))

        content = Path(result_path).read_text(encoding='utf-8')

        assert '# 英伟达H100 GPU深度解析' in content
        assert '**UP主:** TechChannel' in content
        assert '## 📋 内容大纲' in content
        assert '## 💡 核心观点' in content
        assert '## 🏷️ 关键实体' in content

    def test_markdown_contains_detailed_sections(self, tmp_path, sample_report_data):
        """Test Markdown report contains detailed sections."""
        output_path = tmp_path / 'test.md'
        result_path = generate_markdown_report(sample_report_data, str(output_path))

        content = Path(result_path).read_text(encoding='utf-8')

        assert '## 📖 详细内容' in content
        assert '### 英伟达H100 GPU规格介绍' in content

    def test_markdown_contains_charts(self, tmp_path, sample_report_data):
        """Test Markdown report includes chart references."""
        chart = GeneratedChart(
            file_path=str(tmp_path / 'chart.png'),
            chart_type='bar',
            title='Test Chart',
            data_count=3
        )

        sample_report_data.charts = [chart]

        output_path = tmp_path / 'test.md'
        result_path = generate_markdown_report(sample_report_data, str(output_path))

        content = Path(result_path).read_text(encoding='utf-8')

        assert '## 📊 数据可视化' in content
        assert '![Test Chart]' in content

    def test_markdown_contains_fact_checks(self, tmp_path, sample_report_data):
        """Test Markdown report includes fact check results."""
        sample_report_data.fact_checks = [
            {
                'claim': 'Test claim',
                'verified': False,
                'evidence': [],
                'summary': 'Not verified'
            }
        ]

        output_path = tmp_path / 'test.md'
        result_path = generate_markdown_report(sample_report_data, str(output_path))

        content = Path(result_path).read_text(encoding='utf-8')

        assert '## 🔍 事实核查' in content
        assert '**Test claim**' in content
        assert '❌ 未验证' in content


# ============================================================================
# Detailed Sections HTML Tests
# ============================================================================

class TestRenderDetailedSectionsHtml:
    """Tests for _render_detailed_sections_html function."""

    def test_render_empty_list(self):
        """Test rendering empty list returns empty string."""
        result = _render_detailed_sections_html([])
        assert result == ""

    def test_render_single_section(self):
        """Test rendering a single detailed section."""
        sections = [
            {'heading': 'Test Heading', 'content': 'Paragraph 1.\n\nParagraph 2.'}
        ]

        result = _render_detailed_sections_html(sections)

        assert 'Test Heading' in result
        assert 'Paragraph 1.' in result
        assert 'Paragraph 2.' in result
        assert '<div class="detailed-section"' in result
        assert '<h4>' in result
        assert '<p>' in result

    def test_render_multiple_sections(self):
        """Test rendering multiple detailed sections."""
        sections = [
            {'heading': 'Section 1', 'content': 'Content 1'},
            {'heading': 'Section 2', 'content': 'Content 2'},
        ]

        result = _render_detailed_sections_html(sections)

        assert 'Section 1' in result
        assert 'Section 2' in result
        assert result.count('<div class="detailed-section"') == 2

    def test_render_splits_paragraphs(self):
        """Test content is split into paragraphs."""
        sections = [
            {'heading': 'Test', 'content': 'Para 1.\n\nPara 2.\n\nPara 3.'}
        ]

        result = _render_detailed_sections_html(sections)

        assert result.count('<p>') == 3


# ============================================================================
# Charts HTML Tests
# ============================================================================

class TestRenderChartsHtml:
    """Tests for _render_charts_html function."""

    def test_render_empty_list(self):
        """Test rendering empty charts list returns empty string."""
        result = _render_charts_html([], '/output')
        assert result == ""

    def test_render_single_chart(self, tmp_path):
        """Test rendering a single chart."""
        chart = GeneratedChart(
            file_path=str(tmp_path / 'charts' / 'test.png'),
            chart_type='bar',
            title='Test Chart',
            data_count=10
        )

        result = _render_charts_html([chart], str(tmp_path))

        assert 'Test Chart' in result
        assert '10 个数据点' in result
        assert 'charts/test.png' in result
        assert '<div class="chart-container"' in result

    def test_render_multiple_charts(self, tmp_path):
        """Test rendering multiple charts."""
        charts = [
            GeneratedChart(
                file_path=str(tmp_path / 'c1.png'),
                chart_type='bar',
                title='Chart 1',
                data_count=5
            ),
            GeneratedChart(
                file_path=str(tmp_path / 'c2.png'),
                chart_type='line',
                title='Chart 2',
                data_count=3
            ),
        ]

        result = _render_charts_html(charts, str(tmp_path))

        assert result.count('<div class="chart-container"') == 2
        assert 'Chart 1' in result
        assert 'Chart 2' in result


# ============================================================================
# Data Classes Tests
# ============================================================================

class TestDataClasses:
    """Tests for report data classes."""

    def test_fact_check_result_defaults(self):
        """Test FactCheckResult default values."""
        fc = FactCheckResult(
            claim='Test claim',
            verified=True,
            confidence=0.9,
            evidence=['e1'],
            summary='Test summary'
        )

        assert fc.claim == 'Test claim'
        assert fc.verified is True
        assert fc.confidence == 0.9

    def test_related_reading_fields(self):
        """Test RelatedReading fields."""
        rr = RelatedReading(
            title='Test Article',
            url='https://example.com',
            source='Example Site',
            relevance_score=0.95
        )

        assert rr.title == 'Test Article'
        assert rr.url == 'https://example.com'
        assert rr.relevance_score == 0.95

    def test_generated_chart_fields(self):
        """Test GeneratedChart fields."""
        gc = GeneratedChart(
            file_path='/path/to/chart.png',
            chart_type='bar',
            title='Test',
            data_count=5
        )

        assert gc.file_path == '/path/to/chart.png'
        assert gc.chart_type == 'bar'
        assert gc.data_count == 5

    def test_report_data_post_init(self):
        """Test ReportData default values after init."""
        rd = ReportData(
            video_info={'title': 'Test'},
            analysis={'outline': []},
            generated_at='2024-01-01'
        )

        assert rd.fact_checks == []
        assert rd.related_reading == []
        assert rd.charts == []

    def test_detailed_section_post_init(self):
        """Test DetailedSection timestamps default to empty list."""
        ds = DetailedSection(
            heading='Test',
            content='Content'
        )

        assert ds.timestamps == []


# ============================================================================
# Utility Functions Tests
# ============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""

    @patch('shared.report.webbrowser')
    def test_open_report(self, mock_browser):
        """Test open_report opens browser with file URL."""
        open_report('/path/to/report.html')

        mock_browser.open.assert_called_once_with('file:///path/to/report.html')
