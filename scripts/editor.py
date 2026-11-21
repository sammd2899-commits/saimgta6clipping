"""Vertical Clip Editor & Hard ffprobe Verification Engine.

Coordinates rendering through viral_enhancer for 1080x1920 60fps 6 Mbps,
loudnorm -14 LUFS, 2.5s opening hook banner, and word-by-word dynamic captions.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import OUTPUT_DIR, TEMP_DIR, load_active_campaign
from viral_enhancer import enhance_clip, verify_clip_with_ffprobe


def render_vertical_clip(
    segment_path: Path,
    hook_text: str,
    clip_id: int,
    watermark_path: str = None,
    creator_tag: str = "@Creator",
    max_retries: int = 1,
) -> tuple[Path, Path, dict]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    clip_output_path = OUTPUT_DIR / f"clip_{clip_id}.mp4"
    thumb_output_path = OUTPUT_DIR / f"thumb_{clip_id}.jpg"

    valid, _, details = verify_clip_with_ffprobe(clip_output_path)
    if valid and thumb_output_path.exists() and thumb_output_path.stat().st_size > 1024:
        return clip_output_path, thumb_output_path, details

    for attempt in range(max_retries + 1):
        try:
            return enhance_clip(
                segment_path=segment_path,
                hook_text=hook_text,
                output_clip_path=clip_output_path,
                output_thumb_path=thumb_output_path,
                watermark_path=watermark_path,
            )
        except Exception as e:
            if attempt == max_retries:
                raise
