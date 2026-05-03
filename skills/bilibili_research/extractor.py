"""
Bilibili content extractor.
Extracts subtitles and audio from Bilibili videos using yt-dlp.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ExtractResult:
    """Result of Bilibili content extraction."""
    video_id: str
    title: str
    uploader: str
    duration: int  # seconds
    has_subtitles: bool
    subtitles_path: Optional[str] = None
    audio_path: Optional[str] = None
    transcript: Optional[str] = None
    error: Optional[str] = None


def parse_bilibili_url(url: str) -> Optional[str]:
    """
    Extract video ID from Bilibili URL.

    Supports:
    - https://www.bilibili.com/video/BV...
    - https://b23.tv/...
    - https://www.bilibili.com/video/av...
    """
    import re

    # BV format
    bv_match = re.search(r'BV[\w]+', url)
    if bv_match:
        return bv_match.group(0)

    # AV format
    av_match = re.search(r'av(\d+)', url)
    if av_match:
        return f"av{av_match.group(1)}"

    # b23.tv short URL - need to resolve
    if 'b23.tv' in url:
        # For now, return URL as-is and let yt-dlp handle it
        return url

    return None


def get_video_info(url: str, cookies_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get video metadata using yt-dlp.

    Args:
        url: Bilibili video URL
        cookies_path: Optional path to cookies.txt for member videos

    Returns:
        dict with video metadata or None if failed
    """
    cmd = ['yt-dlp', '--dump-json', '--no-playlist']
    if cookies_path:
        cmd.extend(['--cookies', cookies_path])
    cmd.append(url)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None


def check_subtitles(url: str, cookies_path: Optional[str] = None) -> tuple[bool, list[str]]:
    """
    Check if video has subtitles.

    Returns:
        (has_subtitles, available_languages)
    """
    info = get_video_info(url, cookies_path)
    if not info:
        return False, []

    subtitles = info.get('subtitles', {})
    automatic_captions = info.get('automatic_captions', {})

    # Check for Chinese subtitles
    has_zh = (
        'zh-Hans' in subtitles or
        'zh-Hant' in subtitles or
        'zh' in subtitles or
        any('zh' in lang for lang in automatic_captions)
    )

    langs = list(subtitles.keys()) + list(automatic_captions.keys())
    return has_zh, langs


def extract_subtitles(
    url: str,
    output_dir: str,
    cookies_path: Optional[str] = None,
    lang: str = 'zh-Hans'
) -> Optional[str]:
    """
    Download subtitles from Bilibili video.

    Args:
        url: Bilibili video URL
        output_dir: Directory to save subtitles
        cookies_path: Optional cookies.txt for member videos
        lang: Subtitle language preference

    Returns:
        Path to subtitle file (JSON format) or None
    """
    output_dir = Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        'yt-dlp',
        '--write-subs',
        '--write-auto-subs',
        '--sub-lang', lang,
        '--skip-download',
        '--sub-format', 'json3',
        '--output', str(output_dir / '%(id)s.%(ext)s'),
    ]
    if cookies_path:
        cmd.extend(['--cookies', cookies_path])
    cmd.append(url)

    try:
        subprocess.run(cmd, capture_output=True, timeout=60, check=True)
        # Find the downloaded subtitle file
        info = get_video_info(url, cookies_path)
        if info:
            video_id = info.get('id', '')
            sub_path = output_dir / f'{video_id}.zh-Hans.json3'
            if sub_path.exists():
                return str(sub_path)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        pass

    return None


def extract_audio(
    url: str,
    output_dir: str,
    cookies_path: Optional[str] = None,
    audio_format: str = 'm4a'
) -> Optional[str]:
    """
    Download audio from Bilibili video for transcription.

    Args:
        url: Bilibili video URL
        output_dir: Directory to save audio
        cookies_path: Optional cookies.txt for member videos
        audio_format: Audio format (m4a, mp3, wav)

    Returns:
        Path to audio file or None
    """
    output_dir = Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        'yt-dlp',
        '-x',  # extract audio
        '--audio-format', audio_format,
        '--audio-quality', '0',  # best quality
        '--no-playlist',
        '--output', str(output_dir / '%(id)s.%(ext)s'),
    ]
    if cookies_path:
        cmd.extend(['--cookies', cookies_path])
    cmd.append(url)

    try:
        subprocess.run(cmd, capture_output=True, timeout=300, check=True)

        # Find the downloaded audio file
        info = get_video_info(url, cookies_path)
        if info:
            video_id = info.get('id', '')
            # yt-dlp adds extension automatically
            audio_path = output_dir / f'{video_id}.{audio_format}'
            if audio_path.exists():
                return str(audio_path)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, Exception):
        pass

    return None


def parse_subtitle_json(json_path: str) -> str:
    """
    Parse yt-dlp JSON3 subtitle format to plain text.

    Args:
        json_path: Path to JSON3 subtitle file

    Returns:
        Combined subtitle text
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        events = data.get('events', [])
        texts = []
        for event in events:
            if 'segs' in event:
                text = ''.join(seg.get('utf8', '') for seg in event['segs'])
                if text.strip():
                    texts.append(text.strip())

        return ' '.join(texts)
    except (json.JSONDecodeError, KeyError, Exception):
        return ''


def extract(url: str, output_dir: str, cookies_path: Optional[str] = None) -> ExtractResult:
    """
    Main extraction function: get video info, check for subtitles, extract content.

    Args:
        url: Bilibili video URL
        output_dir: Directory for outputs
        cookies_path: Optional cookies.txt

    Returns:
        ExtractResult with all extracted data
    """
    # Get video info
    info = get_video_info(url, cookies_path)
    if not info:
        return ExtractResult(
            video_id='',
            title='',
            uploader='',
            duration=0,
            has_subtitles=False,
            error='Failed to get video info. Check URL or try with cookies for member videos.'
        )

    video_id = info.get('id', '')
    title = info.get('title', 'Unknown')
    uploader = info.get('uploader', 'Unknown')
    duration = info.get('duration', 0)

    # Check subtitles
    has_subs, langs = check_subtitles(url, cookies_path)

    subtitles_path = None
    transcript = None
    audio_path = None

    if has_subs:
        # Try Chinese subtitles first, then any available
        for lang in ['zh-Hans', 'zh-Hant', 'zh'] + langs:
            subtitles_path = extract_subtitles(url, output_dir, cookies_path, lang)
            if subtitles_path:
                transcript = parse_subtitle_json(subtitles_path)
                break

    # If no subtitles or transcription failed, extract audio
    if not transcript:
        audio_path = extract_audio(url, output_dir, cookies_path)

    return ExtractResult(
        video_id=video_id,
        title=title,
        uploader=uploader,
        duration=duration,
        has_subtitles=has_subs,
        subtitles_path=subtitles_path,
        audio_path=audio_path,
        transcript=transcript
    )
