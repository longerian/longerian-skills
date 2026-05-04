"""
Tests for shared.analyzer module.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from shared.analyzer import (
    AnalysisResult,
    EnhancedAnalysisResult,
    DetailedSection,
    DataPoint,
    ChartSpec,
    analyze_content,
    _extract_json,
    _parse_data_points,
    _parse_detailed_sections,
    _generate_chart_specs,
    _create_analysis_prompt
)


# ============================================================================
# Prompt Generation Tests
# ============================================================================

class TestCreateAnalysisPrompt:
    """Tests for _create_analysis_prompt function."""

    def test_basic_prompt_structure(self):
        """Test basic prompt has required sections."""
        prompt = _create_analysis_prompt("test transcript", "Test Title", "Uploader: test", enhanced=False)

        assert "内容大纲" in prompt
        assert "核心观点" in prompt
        assert "关键实体" in prompt
        assert "一句话总结" in prompt

    def test_enhanced_prompt_has_additional_fields(self):
        """Test enhanced prompt includes detailed sections and data points."""
        basic_prompt = _create_analysis_prompt("test", "Title", "", enhanced=False)
        enhanced_prompt = _create_analysis_prompt("test", "Title", "", enhanced=True)

        assert "详细内容" not in basic_prompt
        assert "数据提取" not in basic_prompt
        assert "详细内容" in enhanced_prompt
        assert "数据提取" in enhanced_prompt

    def test_prompt_includes_metadata(self):
        """Test prompt includes metadata when provided."""
        prompt = _create_analysis_prompt("transcript", "Title", "Uploader: test\nDuration: 10:00", enhanced=False)

        assert "Uploader: test" in prompt
        assert "Duration: 10:00" in prompt


# ============================================================================
# JSON Extraction Tests
# ============================================================================

class TestExtractJson:
    """Tests for _extract_json function."""

    def test_extract_valid_json(self):
        """Test extracting valid JSON from response."""
        content = 'Some text before {"key": "value"} some text after'
        result = _extract_json(content)
        assert result == '{"key": "value"}'

    def test_extract_nested_json(self):
        """Test extracting nested JSON."""
        content = 'Text {"outer": {"inner": "value"}}'
        result = _extract_json(content)
        assert result == '{"outer": {"inner": "value"}}'

    def test_no_json_returns_original(self):
        """Test returns original content when no JSON found."""
        content = 'No JSON here, just plain text'
        result = _extract_json(content)
        assert result == 'No JSON here, just plain text'


# ============================================================================
# Data Point Parsing Tests
# ============================================================================

class TestParseDataPoints:
    """Tests for _parse_data_points function."""

    def test_parse_valid_data_points(self):
        """Test parsing valid data points."""
        raw_data = [
            {'label': 'Test', 'value': 100, 'unit': 'GB', 'category': 'Hardware', 'context': 'Test data', 'timestamp': 10},
            {'label': 'Test2', 'value': 200, 'unit': 'MHz', 'category': 'Speed', 'context': '', 'timestamp': None}
        ]

        result = _parse_data_points(raw_data)

        assert len(result) == 2
        assert result[0].label == 'Test'
        assert result[0].value == 100.0
        assert result[0].unit == 'GB'
        assert result[0].category == 'Hardware'
        assert result[0].context == 'Test data'
        assert result[0].timestamp == 10

    def test_parse_handles_invalid_values(self):
        """Test parsing skips invalid data points."""
        raw_data = [
            {'label': 'Valid', 'value': 100, 'unit': 'GB', 'category': '', 'context': ''},
            {'label': 'Invalid', 'value': 'not_a_number', 'unit': 'GB', 'category': '', 'context': ''},
            {'label': 'Missing Value', 'unit': 'GB', 'category': '', 'context': ''}
        ]

        result = _parse_data_points(raw_data)

        assert len(result) == 1
        assert result[0].label == 'Valid'

    def test_parse_empty_list(self):
        """Test parsing empty list returns empty list."""
        assert _parse_data_points([]) == []
        assert _parse_data_points(None) == []


# ============================================================================
# Detailed Section Parsing Tests
# ============================================================================

class TestParseDetailedSections:
    """Tests for _parse_detailed_sections function."""

    def test_parse_valid_sections(self):
        """Test parsing valid detailed sections."""
        raw_data = [
            {'heading': 'Section 1', 'content': 'Content 1', 'timestamps': [0, 30]},
            {'heading': 'Section 2', 'content': 'Content 2', 'timestamps': [60, 90]}
        ]

        result = _parse_detailed_sections(raw_data)

        assert len(result) == 2
        assert result[0].heading == 'Section 1'
        assert result[0].content == 'Content 1'
        assert result[0].timestamps == [0, 30]

    def test_parse_handles_missing_fields(self):
        """Test parsing handles missing optional fields."""
        raw_data = [
            {'heading': 'Test', 'content': 'Content'}
        ]

        result = _parse_detailed_sections(raw_data)

        assert len(result) == 1
        assert result[0].heading == 'Test'
        assert result[0].content == 'Content'
        assert result[0].timestamps == []

    def test_parse_empty_list(self):
        """Test parsing empty list returns empty list."""
        assert _parse_detailed_sections([]) == []
        assert _parse_detailed_sections(None) == []


# ============================================================================
# Chart Spec Generation Tests
# ============================================================================

class TestGenerateChartSpecs:
    """Tests for _generate_chart_specs function."""

    def test_generate_from_empty_data(self):
        """Test generating from empty data points."""
        assert _generate_chart_specs([]) == []

    def test_groups_by_category(self):
        """Test charts are grouped by category."""
        data_points = [
            DataPoint('Item1', 100, 'GB', 'Memory', ''),
            DataPoint('Item2', 200, 'GB', 'Memory', ''),
            DataPoint('Item3', 50, 'TB/s', 'Bandwidth', ''),
        ]

        result = _generate_chart_specs(data_points)

        assert len(result) == 2
        assert any(c.title == 'Memory' for c in result)
        assert any(c.title == 'Bandwidth' for c in result)

    def test_two_items_creates_comparison_table(self):
        """Test two items in a category creates comparison table."""
        data_points = [
            DataPoint('Item1', 100, 'GB', 'Test', ''),
            DataPoint('Item2', 200, 'GB', 'Test', ''),
        ]

        result = _generate_chart_specs(data_points)

        assert len(result) == 1
        assert result[0].chart_type == 'comparison_table'

    def test_no_category_creates_default_chart(self):
        """Test data points without category create default chart."""
        data_points = [
            DataPoint('Item1', 100, 'GB', '', ''),
            DataPoint('Item2', 200, 'GB', '', ''),
        ]

        result = _generate_chart_specs(data_points)

        assert len(result) == 1
        assert result[0].title == '数据概览'


# ============================================================================
# Analysis Function Tests
# ============================================================================

class TestAnalyzeContent:
    """Tests for analyze_content function."""

    @patch('shared.analyzer.OpenAI')
    def test_basic_analysis_returns_analysis_result(self, mock_openai, mock_openai_response):
        """Test basic analysis returns AnalysisResult."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client

        result = analyze_content("test transcript", enhanced=False)

        assert isinstance(result, AnalysisResult)
        assert not isinstance(result, EnhancedAnalysisResult)

    @patch('shared.analyzer.OpenAI')
    def test_enhanced_analysis_returns_enhanced_result(self, mock_openai, mock_openai_response):
        """Test enhanced analysis returns EnhancedAnalysisResult."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client

        result = analyze_content("test transcript", enhanced=True)

        assert isinstance(result, EnhancedAnalysisResult)
        assert hasattr(result, 'detailed_sections')
        assert hasattr(result, 'data_points')

    @patch('shared.analyzer.OpenAI')
    def test_uses_custom_api_key(self, mock_openai, mock_openai_response):
        """Test uses custom API key when provided."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client

        analyze_content("test", api_key="custom-key")

        mock_openai.assert_called_once_with(api_key="custom-key", base_url=None)

    @patch('shared.analyzer.OpenAI')
    def test_uses_custom_base_url(self, mock_openai, mock_openai_response):
        """Test uses custom base URL when provided."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client

        analyze_content("test", base_url="https://custom.api/v1")

        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs['base_url'] == "https://custom.api/v1"

    @patch('shared.analyzer.OpenAI')
    def test_includes_metadata_in_prompt(self, mock_openai, mock_openai_response):
        """Test metadata is included in API prompt."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client

        analyze_content(
            "test",
            metadata={'uploader': 'TestUser', 'duration': '10:00'}
        )

        call_args = mock_client.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        assert 'TestUser' in prompt
        assert '10:00' in prompt


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in analyzer."""

    @patch('shared.analyzer.OpenAI')
    def test_json_decode_error_retries(self, mock_openai):
        """Test retries on JSON decode error."""
        # First call returns invalid JSON, second returns valid JSON
        mock_client = MagicMock()
        invalid_response = MagicMock()
        invalid_response.choices[0].message.content = 'not json'

        valid_response = MagicMock()
        valid_response.choices[0].message.content = '{"outline": [], "summary": ""}'

        mock_client.chat.completions.create.side_effect = [invalid_response, valid_response]
        mock_openai.return_value = mock_client

        result = analyze_content("test", enhanced=False, max_retries=1)

        assert isinstance(result, AnalysisResult)

    @patch('shared.analyzer.OpenAI')
    def test_api_error_raises_runtime_error(self, mock_openai):
        """Test API error raises RuntimeError."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        with pytest.raises(RuntimeError, match="API call failed"):
            analyze_content("test", max_retries=0)
