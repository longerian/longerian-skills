"""
Whisper transcription wrapper for bilibili-research skill.
Embedded for standalone installation - no external dependencies.
GPU-accelerated with automatic CUDA detection.
"""


def transcribe(
    audio_path: str,
    language: str = 'zh',
    model_size: str = 'large-v3-turbo',
    verbose: bool = False
) -> dict:
    """
    Transcribe audio using Whisper with GPU acceleration.

    Args:
        audio_path: Path to audio file
        language: Language code (default: 'zh' for Chinese)
        model_size: Model size (default: large-v3-turbo for best accuracy)
        verbose: Print progress

    Returns:
        dict with keys:
        - text: str (full transcript)
        - segments: list[dict] (timestamped segments)
        - language: str
        - duration: float
    """
    import whisper
    import torch

    # GPU detection
    if verbose:
        has_cuda = torch.cuda.is_available()
        if has_cuda:
            print(f"[GPU] Using CUDA: {torch.cuda.get_device_name(0)}")
        else:
            print("[WARNING] CUDA not available, using CPU (slow)")
            print("         For GPU acceleration:")
            print("         - Use Python 3.12 (not 3.14)")
            print("         - Install PyTorch with CUDA:")
            print("           pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")

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
