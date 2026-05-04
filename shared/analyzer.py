"""
Shared AI content analysis module.
Uses OpenAI-compatible API (GLM, Claude, etc.) to analyze transcripts.
Enhanced version with detailed content extraction and data visualization.
"""

import os
import json
from typing import Optional, Any
from dataclasses import dataclass, field
from openai import OpenAI


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class DataPoint:
    """A numerical data point mentioned in the content."""
    label: str           # Label for the data (e.g., "Nvidia H100 内存带宽")
    value: float         # Numerical value
    unit: str = ""       # Unit (e.g., "GB/s", "亿美元", "nm")
    category: str = ""   # Category for grouping (e.g., "硬件规格", "财务数据")
    context: str = ""    # Context from the content
    timestamp: Optional[int] = None  # Position in video (seconds)


@dataclass
class ChartSpec:
    """Specification for generating a chart from data points."""
    chart_type: str      # "bar", "line", "comparison_table"
    title: str           # Chart title
    data_points: list[DataPoint]
    metadata: dict = field(default_factory=dict)  # Additional config


@dataclass
class DetailedSection:
    """A detailed section with full content (3-5 paragraphs)."""
    heading: str                  # Section heading
    content: str                  # Full content (3-5 paragraphs)
    timestamps: list[int] = field(default_factory=list)  # Related video positions


@dataclass
class AnalysisResult:
    """Basic analysis result (backward compatible)."""
    outline: list[str]              # Content outline (5-7 points)
    core_points: list[str]          # Core insights (3-5 points)
    key_entities: list[str]         # Key entities (people, places, terms)
    verifiable_claims: list[str]    # Verifiable statements for fact-checking
    keywords: list[str]             # Keywords for extended reading
    summary: str                    # One-line summary


@dataclass
class EnhancedAnalysisResult:
    """Enhanced analysis result with detailed content and data visualization."""
    # Basic fields (from AnalysisResult)
    outline: list[str]              # Content outline (5-7 points)
    core_points: list[str]          # Core insights (3-5 points)
    key_entities: list[str]         # Key entities (people, places, terms)
    verifiable_claims: list[str]    # Verifiable statements for fact-checking
    keywords: list[str]             # Keywords for extended reading
    summary: str                    # One-line summary

    # Enhanced fields
    detailed_sections: list[DetailedSection]  # Detailed content (3-5 paragraphs each)
    data_points: list[DataPoint]              # Numerical data extracted from content
    chart_specs: list[ChartSpec]              # Chart generation specifications


# ============================================================================
# Analysis Functions
# ============================================================================

def _create_analysis_prompt(
    transcript: str,
    title: str,
    meta_str: str,
    enhanced: bool = True
) -> str:
    """Create the analysis prompt."""
    if enhanced:
        return f"""请分析以下视频/音频转录文本，提取：

1. 内容大纲（5-7条，按时间顺序，每条15-30字）
2. 核心观点（3-5条，UP主主要想表达什么）
3. 关键实体（人名、地名、机构名、技术名词）
4. 可验证陈述（可以联网验证的事实陈述，3-5条）
5. 关键词（用于搜索相关资料，5-10个）
6. 一句话总结（20-50字）

7. 详细内容（对每个大纲要点，直接写出视频中的具体知识点和信息）

**重要**：详细内容必须直接输出实质性的知识，用第三人称客观陈述。

❌ 错误示例（不要这样写）：
- "视频介绍了Celebries公司的上市情况"
- "UP主提到了公司的创始团队"
- "视频中分析了AI芯片的技术路线"

✅ 正确示例（应该这样写）：
- "Celebries公司预计于2024年5月中旬上市，上市代码为CBRS。公司估值从上一轮的231亿美元上升至预计的351亿美元，涨幅约52%。"
- "公司五位联合创始人在创立Celebries之前已合作近十年。CEO Andrew Feldman曾创立SeaMicro，该公司于2012年被AMD以3.3亿美元收购。"
- "Celebries采用晶圆级芯片（Wafer-Scale Engine，WSE）技术路线，与Nvidia的GPU架构不同。WSE将整个晶圆作为单颗芯片，面积约为Nvidia H100 GPU的56倍。"

8. 数据提取（提取视频中提到的所有数值数据，包括标签、数值、单位、分类和上下文）

标题: {title}
{meta_str}

转录文本:
{transcript}

请以JSON格式返回，格式如下：
{{
  "outline": ["要点1", "要点2", ...],
  "core_points": ["观点1", "观点2", ...],
  "key_entities": ["实体1", "实体2", ...],
  "verifiable_claims": ["陈述1", "陈述2", ...],
  "keywords": ["关键词1", "关键词2", ...],
  "summary": "一句话总结",
  "detailed_sections": [
    {{
      "heading": "大纲要点1",
      "content": "详细内容段落1。\\n\\n详细内容段落2。\\n\\n详细内容段落3。",
      "timestamps": [0, 120]
    }}
  ],
  "data_points": [
    {{
      "label": "数据标签",
      "value": 123.45,
      "unit": "单位",
      "category": "分类",
      "context": "数据出现的上下文说明",
      "timestamp": 60
    }}
  ]
}}

只返回JSON，不要其他文字。"""
    else:
        return f"""请分析以下视频/音频转录文本，提取：

1. 内容大纲（5-7条，按时间顺序）
2. 核心观点（3-5条，UP主主要想表达什么）
3. 关键实体（人名、地名、机构名、技术名词）
4. 可验证陈述（可以联网验证的事实陈述，3-5条）
5. 关键词（用于搜索相关资料，5-10个）
6. 一句话总结

标题: {title}
{meta_str}

转录文本:
{transcript}

请以JSON格式返回，格式如下：
{{
  "outline": ["要点1", "要点2", ...],
  "core_points": ["观点1", "观点2", ...],
  "key_entities": ["实体1", "实体2", ...],
  "verifiable_claims": ["陈述1", "陈述2", ...],
  "keywords": ["关键词1", "关键词2", ...],
  "summary": "一句话总结"
}}

只返回JSON，不要其他文字。"""


def _extract_json(content: str) -> str:
    """Extract JSON from response content."""
    start = content.find('{')
    end = content.rfind('}') + 1
    if start >= 0 and end > start:
        return content[start:end]
    return content


def _parse_data_points(raw_data: list) -> list[DataPoint]:
    """Parse raw data points into DataPoint objects."""
    data_points = []
    for item in raw_data or []:
        try:
            # Skip items with missing value
            if 'value' not in item or item['value'] is None:
                continue
            data_points.append(DataPoint(
                label=item.get('label', ''),
                value=float(item['value']),
                unit=item.get('unit', ''),
                category=item.get('category', ''),
                context=item.get('context', ''),
                timestamp=item.get('timestamp')
            ))
        except (ValueError, TypeError):
            continue
    return data_points


def _parse_detailed_sections(raw_data: list) -> list[DetailedSection]:
    """Parse raw detailed sections into DetailedSection objects."""
    sections = []
    for item in raw_data or []:
        sections.append(DetailedSection(
            heading=item.get('heading', ''),
            content=item.get('content', ''),
            timestamps=item.get('timestamps', [])
        ))
    return sections


def _generate_chart_specs(data_points: list[DataPoint]) -> list[ChartSpec]:
    """Generate chart specifications from data points."""
    if not data_points:
        return []

    charts = []
    categories = set(dp.category for dp in data_points if dp.category)

    # Group by category
    for category in categories:
        category_data = [dp for dp in data_points if dp.category == category]

        # Determine chart type based on data
        if len(category_data) == 2:
            chart_type = "comparison_table"
        elif len(category_data) > 10:
            chart_type = "bar"
        else:
            chart_type = "bar"

        charts.append(ChartSpec(
            chart_type=chart_type,
            title=category or "数据概览",
            data_points=category_data,
            metadata={"category": category}
        ))

    # If no categories, create one overview chart
    if not charts:
        charts.append(ChartSpec(
            chart_type="bar",
            title="数据概览",
            data_points=data_points[:10],  # Limit to 10 items
            metadata={}
        ))

    return charts


def analyze_content(
    transcript: str,
    title: str = "",
    metadata: Optional[dict] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: str = "glm-4-flash",
    enhanced: bool = True,
    timeout: int = 300,
    max_retries: int = 2
) -> AnalysisResult | EnhancedAnalysisResult:
    """
    Analyze transcript using OpenAI-compatible API (GLM, Claude, etc.).

    Args:
        transcript: Text content to analyze
        title: Content title for context
        metadata: Additional context (uploader, duration, etc.)
        api_key: API key (default: OPENAI_API_KEY or ANTHROPIC_API_KEY env var)
        base_url: API base URL (default: OPENAI_API_BASE env var)
        model: Model name (default: glm-4-flash)
        enhanced: If True, return EnhancedAnalysisResult with detailed content
        timeout: Request timeout in seconds
        max_retries: Number of retries on failure

    Returns:
        AnalysisResult or EnhancedAnalysisResult with extracted insights
    """
    # Configure API client
    # Check multiple env vars: api_key param > ZHIPU_API_KEY > OPENAI_API_KEY > ANTHROPIC_API_KEY
    # Default base URL is GLM coding endpoint
    client = OpenAI(
        api_key=api_key or os.environ.get('ZHIPU_API_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY'),
        base_url=base_url or os.environ.get('OPENAI_API_BASE') or os.environ.get('ZHIPU_API_BASE', 'https://open.bigmodel.cn/api/coding/paas/v4')
    )

    # Build metadata string
    meta_str = ""
    if metadata:
        meta_str = "\n".join(f"{k}: {v}" for k, v in metadata.items())

    # Create prompt
    prompt = _create_analysis_prompt(transcript, title, meta_str, enhanced)

    # API call with error handling
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': '你是一个专业的内容分析助手，擅长从视频转录文本中提取关键信息和数据。**重要**：生成详细内容时，直接输出具体的知识点、事实和数据，用第三人称客观陈述。绝对不要说"视频介绍了""UP主提到""视频中说道"等元描述语言。读者想直接获得知识，而不是知道视频讲了什么。'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.3,
                timeout=timeout
            )

            content = response.choices[0].message.content
            json_str = _extract_json(content)
            data = json.loads(json_str)

            # Parse response
            if enhanced:
                detailed_sections = _parse_detailed_sections(data.get('detailed_sections', []))
                data_points = _parse_data_points(data.get('data_points', []))
                chart_specs = _generate_chart_specs(data_points)

                return EnhancedAnalysisResult(
                    outline=data.get('outline', []),
                    core_points=data.get('core_points', []),
                    key_entities=data.get('key_entities', []),
                    verifiable_claims=data.get('verifiable_claims', []),
                    keywords=data.get('keywords', []),
                    summary=data.get('summary', ''),
                    detailed_sections=detailed_sections,
                    data_points=data_points,
                    chart_specs=chart_specs
                )
            else:
                return AnalysisResult(
                    outline=data.get('outline', []),
                    core_points=data.get('core_points', []),
                    key_entities=data.get('key_entities', []),
                    verifiable_claims=data.get('verifiable_claims', []),
                    keywords=data.get('keywords', []),
                    summary=data.get('summary', '')
                )

        except json.JSONDecodeError as e:
            last_error = e
            if attempt < max_retries:
                # Retry with simpler prompt
                prompt = "请以JSON格式返回分析结果，只包含outline和summary字段。\n\n" + prompt
                continue
            else:
                raise ValueError(f"Failed to parse API response as JSON: {e}") from e

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                continue
            else:
                raise RuntimeError(f"API call failed after {max_retries + 1} attempts: {e}") from e

    # Should not reach here
    raise RuntimeError(f"Unexpected error: {last_error}")
