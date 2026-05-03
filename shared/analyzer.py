"""
Shared AI content analysis module.
Uses Claude API to analyze transcripts and extract key information.
"""

import os
from typing import Optional
from dataclasses import dataclass
from anthropic import Anthropic


@dataclass
class AnalysisResult:
    """Result of content analysis."""
    outline: list[str]              # Content outline (5-7 points)
    core_points: list[str]          # Core insights (3-5 points)
    key_entities: list[str]         # Key entities (people, places, terms)
    verifiable_claims: list[str]    # Verifiable statements for fact-checking
    keywords: list[str]             # Keywords for extended reading
    summary: str                    # One-line summary


def analyze_content(
    transcript: str,
    title: str = "",
    metadata: Optional[dict] = None,
    api_key: Optional[str] = None
) -> AnalysisResult:
    """
    Analyze transcript using Claude API.

    Args:
        transcript: Text content to analyze
        title: Content title for context
        metadata: Additional context (uploader, duration, etc.)
        api_key: Anthropic API key (default: ANTHROPIC_API_KEY env var)

    Returns:
        AnalysisResult with extracted insights
    """
    client = Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))

    meta_str = ""
    if metadata:
        meta_str = "\n".join(f"{k}: {v}" for k, v in metadata.items())

    prompt = f"""请分析以下视频/音频转录文本，提取：

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

    response = client.messages.create(
        model='claude-sonnet-4-20250514',
        max_tokens=4000,
        messages=[{'role': 'user', 'content': prompt}]
    )

    import json
    content = response.content[0].text

    # Extract JSON from response (in case there's extra text)
    start = content.find('{')
    end = content.rfind('}') + 1
    if start >= 0 and end > start:
        content = content[start:end]

    data = json.loads(content)

    return AnalysisResult(
        outline=data.get('outline', []),
        core_points=data.get('core_points', []),
        key_entities=data.get('key_entities', []),
        verifiable_claims=data.get('verifiable_claims', []),
        keywords=data.get('keywords', []),
        summary=data.get('summary', '')
    )
