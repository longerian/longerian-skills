"""
Shared Whisper transcription wrapper.
Uses Whisper for audio transcription.
"""

import os
from pathlib import Path
from typing import Optional


def transcribe(
    audio_path: str,
    language: str = 'zh',
    model_size: str = 'base',
    verbose: bool = False
) -> dict:
    """
    Transcribe audio using Whisper.

    Args:
        audio_path: Path to audio file
        language: Language code (default: 'zh' for Chinese)
        model_size: Model size (tiny, base, small, medium, large, large-v3-turbo)
        verbose: Print progress

    Returns:
        dict with keys:
        - text: str (full transcript)
        - segments: list[dict] (timestamped segments)
        - language: str
        - duration: float
    """
    import whisper

    if verbose:
        print(f"Loading Whisper model: {model_size}...")

    model = whisper.load_model(model_size)

    if verbose:
        print("Transcribing...")

    result = model.transcribe(
        audio_path,
        language=language,
        verbose=verbose
    )

    return {
        'text': result['text'],
        'segments': result['segments'],
        'language': result.get('language', language),
        'duration': sum(s['end'] - s['start'] for s in result['segments'])
    }
