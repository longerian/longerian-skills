"""
Pytest configuration and fixtures for longerian-skills tests.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_transcript():
    """Sample video transcript for testing."""
    return """
    今天我们来聊一聊英伟达的GPU架构。英伟达最新的H100 GPU拥有80GB的HBM3内存，
    带宽达到了3.35TB/s，相比上一代A100的2TB/s有了大幅提升。

    在人工智能训练领域，H100的表现非常出色。根据MLPerf基准测试，
    H100在GPT-3训练上的性能比A100快了4倍。

    不过价格也不菲，单片H100的售价大约在3万美元左右，而A100的价格是1.5万美元。
    对于大型数据中心来说，这是一笔巨大的投资。

    除了英伟达，AMD和Intel也在积极布局AI芯片市场。
    AMD的MI300X采用了192GB的HBM3内存，带宽达到了5.3TB/s。
    """


@pytest.fixture
def sample_video_info():
    """Sample video metadata."""
    return {
        'title': '英伟达H100 GPU深度解析',
        'uploader': 'TechChannel',
        'duration_str': '35分20秒',
        'url': 'https://www.bilibili.com/video/BV1234567890'
    }


# ============================================================================
# Analysis Result Fixtures
# ============================================================================

@pytest.fixture
def sample_analysis_result():
    """Sample basic analysis result."""
    from shared.analyzer import AnalysisResult

    return AnalysisResult(
        outline=[
            '英伟达H100 GPU规格介绍',
            '与A100性能对比',
            '价格分析',
            '竞争对手产品'
        ],
        core_points=[
            'H100拥有80GB HBM3内存，带宽3.35TB/s',
            'H100在GPT-3训练上比A100快4倍',
            'H100售价约3万美元'
        ],
        key_entities=['英伟达', 'H100', 'A100', 'AMD', 'MI300X', 'HBM3', 'MLPerf', 'GPT-3'],
        verifiable_claims=[
            'H100带宽为3.35TB/s',
            'H100售价约3万美元'
        ],
        keywords=['GPU', '英伟达', 'H100', 'AI训练', 'HBM3'],
        summary='英伟达H100 GPU在AI训练领域表现强劲，但价格较高。'
    )


@pytest.fixture
def sample_enhanced_analysis_result():
    """Sample enhanced analysis result with detailed sections and data points."""
    from shared.analyzer import EnhancedAnalysisResult, DetailedSection, DataPoint, ChartSpec

    return EnhancedAnalysisResult(
        outline=['英伟达H100 GPU规格介绍', '与A100性能对比', '价格分析', '竞争对手产品'],
        core_points=[
            'H100拥有80GB HBM3内存，带宽3.35TB/s',
            'H100在GPT-3训练上比A100快4倍',
            'H100售价约3万美元'
        ],
        key_entities=['英伟达', 'H100', 'A100', 'AMD', 'MI300X', 'HBM3', 'MLPerf', 'GPT-3'],
        verifiable_claims=['H100带宽为3.35TB/s', 'H100售价约3万美元'],
        keywords=['GPU', '英伟达', 'H100', 'AI训练', 'HBM3'],
        summary='英伟达H100 GPU在AI训练领域表现强劲，但价格较高。',
        detailed_sections=[
            DetailedSection(
                heading='英伟达H100 GPU规格介绍',
                content='英伟达H100是当前最强大的AI训练GPU之一。它配备了80GB的HBM3内存，\n\n带宽高达3.35TB/s，相比前代产品有显著提升。\n\n这种规格使其能够处理更大规模的模型训练任务。',
                timestamps=[0, 60]
            ),
            DetailedSection(
                heading='与A100性能对比',
                content='根据MLPerf基准测试数据，H100在GPT-3模型训练上的表现。\n\n相比A100提升了4倍之多，这是一个巨大的性能飞跃。\n\n对于需要快速迭代的大模型训练场景来说，这种提升非常有价值。',
                timestamps=[120, 240]
            )
        ],
        data_points=[
            DataPoint(label='H100 内存容量', value=80, unit='GB', category='硬件规格', context='H100配备的HBM3内存容量'),
            DataPoint(label='H100 带宽', value=3.35, unit='TB/s', category='硬件规格', context='H100的内存带宽'),
            DataPoint(label='A100 带宽', value=2.0, unit='TB/s', category='硬件规格', context='A100的内存带宽'),
            DataPoint(label='H100 性能提升', value=4.0, unit='x', category='性能对比', context='相比A100的性能提升倍数'),
            DataPoint(label='H100 售价', value=30000, unit='美元', category='价格', context='单片H100的售价'),
            DataPoint(label='A100 售价', value=15000, unit='美元', category='价格', context='单片A100的售价'),
        ],
        chart_specs=[
            ChartSpec(
                chart_type='bar',
                title='硬件规格对比',
                data_points=[]
            ),
            ChartSpec(
                chart_type='comparison_table',
                title='价格对比',
                data_points=[]
            )
        ]
    )


# ============================================================================
# API Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''{
  "outline": ["要点1", "要点2", "要点3"],
  "core_points": ["观点1", "观点2"],
  "key_entities": ["实体1", "实体2"],
  "verifiable_claims": ["陈述1"],
  "keywords": ["关键词1", "关键词2"],
  "summary": "总结",
  "detailed_sections": [
    {
      "heading": "章节1",
      "content": "详细内容。",
      "timestamps": [0, 60]
    }
  ],
  "data_points": [
    {
      "label": "数据1",
      "value": 100,
      "unit": "GB",
      "category": "分类",
      "context": "说明"
    }
  ]
}'''
    return mock_response


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Mock OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    return mock_client


# ============================================================================
# Report Data Fixtures
# ============================================================================

@pytest.fixture
def sample_report_data(sample_video_info, sample_enhanced_analysis_result):
    """Sample report data."""
    from shared.report import ReportData

    analysis_dict = {
        'outline': sample_enhanced_analysis_result.outline,
        'core_points': sample_enhanced_analysis_result.core_points,
        'key_entities': sample_enhanced_analysis_result.key_entities,
        'verifiable_claims': sample_enhanced_analysis_result.verifiable_claims,
        'keywords': sample_enhanced_analysis_result.keywords,
        'summary': sample_enhanced_analysis_result.summary,
        'detailed_sections': [
            {
                'heading': ds.heading,
                'content': ds.content,
                'timestamps': ds.timestamps
            }
            for ds in sample_enhanced_analysis_result.detailed_sections
        ],
        'data_points': [
            {
                'label': dp.label,
                'value': dp.value,
                'unit': dp.unit,
                'category': dp.category,
                'context': dp.context
            }
            for dp in sample_enhanced_analysis_result.data_points
        ]
    }

    return ReportData(
        video_info=sample_video_info,
        analysis=analysis_dict,
        fact_checks=[],
        related_reading=[],
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        charts=[]
    )


# ============================================================================
# Environment Setup
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    """Setup test environment for each test."""
    # Set test output directory
    test_output = tmp_path / 'output'
    test_output.mkdir()

    monkeypatch.setenv('TEST_OUTPUT_DIR', str(test_output))

    # Ensure API keys are set to dummy values for testing
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-key')

    yield test_output
