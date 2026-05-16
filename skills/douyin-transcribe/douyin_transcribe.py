#!/usr/bin/env python3
"""
Douyin Video Transcription with Whisper (GPU Accelerated)
Usage: python douyin_transcribe.py <douyin_url>
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Check GPU availability
try:
    import torch
    HAS_CUDA = torch.cuda.is_available()
    if HAS_CUDA:
        print(f"[GPU] Using CUDA: {torch.cuda.get_device_name(0)}")
    else:
        print("[WARNING] CUDA not available, using CPU (slow)")
except ImportError:
    HAS_CUDA = False
    print("[WARNING] PyTorch not installed")

try:
    import whisper
except ImportError:
    print("[ERROR] whisper not installed. Run: pip install openai-whisper")
    sys.exit(1)

# Configuration
HOME = Path.home()
OUTPUT_DIR = HOME / ".longerian" / "data" / "douyin"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def transcribe_video(video_path: str, model_size: str = "large-v3-turbo"):
    """Transcribe video using Whisper."""
    print(f"\n[1/3] Loading Whisper model ({model_size})...")
    start = time.time()
    model = whisper.load_model(model_size)
    print(f"      Model loaded in {time.time() - start:.1f}s")

    print(f"\n[2/3] Transcribing video...")
    start = time.time()
    result = model.transcribe(video_path, language="zh", verbose=False)
    duration = time.time() - start

    print(f"      Done in {duration:.1f}s")

    return result


def save_transcript(result, video_title: str, output_dir: Path):
    """Save transcript to text and markdown files."""
    # Save raw transcript
    txt_path = output_dir / f"{video_title}-transcript.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"])

    # Save with timestamps
    segments_path = output_dir / f"{video_title}-segments.txt"
    with open(segments_path, "w", encoding="utf-8") as f:
        for seg in result["segments"]:
            f.write(f"[{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}\n")

    print(f"\n[3/3] Saved:")
    print(f"      - {txt_path}")
    print(f"      - {segments_path}")


def main():
    parser = argparse.ArgumentParser(description="Transcribe Douyin video with Whisper")
    parser.add_argument("video", help="Path to video file or Douyin URL")
    parser.add_argument("--model", default="large-v3-turbo", help="Whisper model size")
    parser.add_argument("--output", help="Output directory (default: ~/.longerian/data/douyin)")
    args = parser.parse_args()

    video_path = args.video

    # Check if it's a URL or local file
    if video_path.startswith("http"):
        print("[ERROR] URL download not yet supported.")
        print("        Please download the video first using Playwright, then run:")
        print(f"        python {sys.argv[0]} <path_to_video.mp4>")
        sys.exit(1)

    # Check if file exists
    if not Path(video_path).exists():
        print(f"[ERROR] Video file not found: {video_path}")
        sys.exit(1)

    # Set output directory
    output_dir = Path(args.output) if args.output else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    video_name = Path(video_path).stem
    video_title = f"douyin-{int(time.time())}"

    # Transcribe
    result = transcribe_video(video_path, args.model)

    # Save results
    save_transcript(result, video_title, output_dir)

    # Print stats
    duration = result["segments"][-1]["end"]
    print(f"\n[Stats]")
    print(f"      Video length: {duration:.1f}s ({duration/60:.1f}min)")
    print(f"      Text length: {len(result['text'])} chars")
    print(f"      Segments: {len(result['segments'])}")


if __name__ == "__main__":
    main()
