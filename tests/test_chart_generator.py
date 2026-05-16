"""
Tests for shared.chart_generator module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from shared.chart_generator import (
    GeneratedChart,
    generate_bar_chart,
    generate_line_chart,
    generate_comparison_table,
    generate_charts,
    chart_to_html,
    chart_to_markdown
)
from shared.analyzer import DataPoint, ChartSpec


# ============================================================================
# Bar Chart Tests
# ============================================================================

class TestGenerateBarChart:
    """Tests for generate_bar_chart function."""

    def test_generate_bar_chart_creates_file(self, tmp_path):
        """Test bar chart generation creates a PNG file."""
        data_points = [
            DataPoint('Item 1', 100, 'GB', 'Hardware', 'Test'),
            DataPoint('Item 2', 200, 'GB', 'Hardware', 'Test'),
            DataPoint('Item 3', 150, 'GB', 'Hardware', 'Test'),
        ]

        result = generate_bar_chart(data_points, 'Test Chart', str(tmp_path))

        assert isinstance(result, GeneratedChart)
        assert result.chart_type == 'bar'
        assert result.title == 'Test Chart'
        assert result.data_count == 3
        assert Path(result.file_path).exists()
        assert result.file_path.endswith('.png')

    def test_bar_chart_limits_to_15_items(self, tmp_path):
        """Test bar chart limits data to 15 items."""
        data_points = [DataPoint(f'Item{i}', i, 'unit', 'cat', '') for i in range(20)]

        result = generate_bar_chart(data_points, 'Test', str(tmp_path))

        # Should only include top 15 by value
        assert result.data_count == 15

    def test_bar_chart_sorts_by_value(self, tmp_path):
        """Test bar chart sorts data by value descending."""
        data_points = [
            DataPoint('Low', 10, '', '', ''),
            DataPoint('High', 100, '', '', ''),
            DataPoint('Mid', 50, '', '', ''),
        ]

        result = generate_bar_chart(data_points, 'Test', str(tmp_path))

        assert result.data_count == 3
        # File should be created
        assert Path(result.file_path).exists()

    def test_bar_chart_empty_data_raises_error(self, tmp_path):
        """Test bar chart with empty data raises ValueError."""
        with pytest.raises(ValueError, match="No data points"):
            generate_bar_chart([], 'Test', str(tmp_path))


# ============================================================================
# Line Chart Tests
# ============================================================================

class TestGenerateLineChart:
    """Tests for generate_line_chart function."""

    def test_generate_line_chart_creates_file(self, tmp_path):
        """Test line chart generation creates a PNG file."""
        data_points = [
            DataPoint('T1', 100, 'GB', '', '', timestamp=0),
            DataPoint('T2', 150, 'GB', '', '', timestamp=10),
            DataPoint('T3', 200, 'GB', '', '', timestamp=20),
        ]

        result = generate_line_chart(data_points, 'Time Series', str(tmp_path))

        assert isinstance(result, GeneratedChart)
        assert result.chart_type == 'line'
        assert result.title == 'Time Series'
        assert Path(result.file_path).exists()

    def test_line_chart_sorts_by_timestamp(self, tmp_path):
        """Test line chart sorts by timestamp."""
        data_points = [
            DataPoint('T3', 300, '', '', '', timestamp=30),
            DataPoint('T1', 100, '', '', '', timestamp=10),
            DataPoint('T2', 200, '', '', '', timestamp=20),
        ]

        result = generate_line_chart(data_points, 'Test', str(tmp_path))

        assert result.data_count == 3

    def test_line_chart_handles_no_timestamp(self, tmp_path):
        """Test line chart handles missing timestamps."""
        data_points = [
            DataPoint('A', 100, '', '', ''),
            DataPoint('B', 200, '', '', ''),
        ]

        result = generate_line_chart(data_points, 'Test', str(tmp_path))

        assert result.data_count == 2

    def test_line_chart_empty_data_raises_error(self, tmp_path):
        """Test line chart with empty data raises ValueError."""
        with pytest.raises(ValueError, match="No data points"):
            generate_line_chart([], 'Test', str(tmp_path))


# ============================================================================
# Comparison Table Tests
# ============================================================================

class TestGenerateComparisonTable:
    """Tests for generate_comparison_table function."""

    def test_generate_table_creates_file(self, tmp_path):
        """Test comparison table generation creates a PNG file."""
        data_points = [
            DataPoint('Item A', 100, 'GB', 'Hardware', 'Description A'),
            DataPoint('Item B', 200, 'GB', 'Hardware', 'Description B'),
        ]

        result = generate_comparison_table(data_points, 'Comparison', str(tmp_path))

        assert isinstance(result, GeneratedChart)
        assert result.chart_type == 'comparison_table'
        assert result.title == 'Comparison'
        assert Path(result.file_path).exists()

    def test_table_limits_to_10_rows(self, tmp_path):
        """Test comparison table limits to 10 rows."""
        data_points = [DataPoint(f'Item{i}', i, 'unit', 'cat', 'desc') for i in range(15)]

        result = generate_comparison_table(data_points, 'Test', str(tmp_path))

        assert result.data_count == 10

    def test_table_empty_data_raises_error(self, tmp_path):
        """Test comparison table with empty data raises ValueError."""
        with pytest.raises(ValueError, match="No data points"):
            generate_comparison_table([], 'Test', str(tmp_path))


# ============================================================================
# Multi-Chart Generation Tests
# ============================================================================

class TestGenerateCharts:
    """Tests for generate_charts function."""

    def test_generate_multiple_charts(self, tmp_path):
        """Test generating multiple charts from specifications."""
        chart_specs = [
            ChartSpec('bar', 'Bar Chart', [
                DataPoint('A', 100, '', '', ''),
                DataPoint('B', 200, '', '', ''),
            ]),
            ChartSpec('comparison_table', 'Table', [
                DataPoint('X', 50, '', '', ''),
            ]),
        ]

        result = generate_charts(chart_specs, str(tmp_path))

        assert len(result) == 2
        assert all(isinstance(c, GeneratedChart) for c in result)
        assert all(Path(c.file_path).exists() for c in result)

    def test_generate_charts_handles_failure_gracefully(self, tmp_path, capsys):
        """Test chart generation continues on individual failures."""
        chart_specs = [
            ChartSpec('bar', 'Valid Chart', [
                DataPoint('A', 100, '', '', ''),
            ]),
            ChartSpec('bar', 'Invalid Chart', []),  # Empty data will fail
            ChartSpec('bar', 'Another Valid', [
                DataPoint('B', 200, '', '', ''),
            ]),
        ]

        result = generate_charts(chart_specs, str(tmp_path))

        # Should generate 2 charts (skip the invalid one)
        assert len(result) == 2

    def test_generate_charts_empty_list(self, tmp_path):
        """Test generating charts from empty list."""
        result = generate_charts([], str(tmp_path))
        assert result == []

    def test_unknown_chart_type_defaults_to_bar(self, tmp_path):
        """Test unknown chart type defaults to bar chart."""
        chart_specs = [
            ChartSpec('unknown_type', 'Test', [
                DataPoint('A', 100, '', '', ''),
            ]),
        ]

        result = generate_charts(chart_specs, str(tmp_path))

        assert len(result) == 1
        assert result[0].chart_type == 'bar'


# ============================================================================
# HTML/Markdown Conversion Tests
# ============================================================================

class TestChartConversions:
    """Tests for chart_to_html and chart_to_markdown functions."""

    def test_chart_to_html_without_base_dir(self):
        """Test HTML conversion uses absolute path."""
        chart = GeneratedChart('/path/to/chart.png', 'bar', 'Test Chart', 5)

        html = chart_to_html(chart)

        assert '/path/to/chart.png' in html
        assert 'Test Chart' in html
        assert '5 个数据点' in html
        assert '<div class="chart-container"' in html
        assert '<img src=' in html

    def test_chart_to_html_with_base_dir(self):
        """Test HTML conversion uses relative path when base_dir provided."""
        chart = GeneratedChart('/output/charts/chart.png', 'bar', 'Test', 3)

        html = chart_to_html(chart, base_dir='/output')

        assert 'charts/chart.png' in html

    def test_chart_to_markdown_without_base_dir(self):
        """Test Markdown conversion uses absolute path."""
        chart = GeneratedChart('/path/to/chart.png', 'bar', 'Test Chart', 5)

        md = chart_to_markdown(chart)

        assert '/path/to/chart.png' in md
        assert 'Test Chart' in md
        assert '5' in md
        assert '### Test Chart' in md

    def test_chart_to_markdown_with_base_dir(self):
        """Test Markdown conversion uses relative path when base_dir provided."""
        chart = GeneratedChart('/output/charts/chart.png', 'bar', 'Test', 3)

        md = chart_to_markdown(chart, base_dir='/output')

        assert 'charts/chart.png' in md
