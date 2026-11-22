"""Vertical Clip Editor & Hard ffprobe Verification Engine.

Transforms 16:9 targeted stream segments into viral 9:16 (1080x1920) clips with:
- Top Hook Card (bold text + red accent keywords)
- Centered gameplay + blurred backdrop
- Audio loudness normalization (loudnorm)
- Active campaign watermark support
- High-contrast vertical thumbnail extraction
- HARD Python ffprobe verification (resolution, audio, 10s-59s duration check)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import OUTPUT_DIR, TEMP_DIR, load_active_campaign
from viral_enhancer import enhance_clip

FONT_PATHS = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
]


def get_font(size: int = 42):
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_hook_card(hook_text: str, output_path: Path, creator_tag: str = "@Creator") -> Path:
    """Renders a viral hook card with rounded corners, white text, and red accent words."""
    card_w, card_h = 960, 230
    img = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded card background with subtle red border
    draw.rounded_rectangle(
        [5, 5, card_w - 5, card_h - 5],
        radius=28,
        fill=(14, 14, 18, 238),
        outline=(255, 59, 59, 210),
        width=3,
    )

    font_main = get_font(42)
    font_tag = get_font(26)

    # Word wrapping
    words = hook_text.split()
    lines = []
    cur_line = []
    for w in words:
        test_line = " ".join(cur_line + [w]).replace("*", "")
        bbox = draw.textbbox((0, 0), test_line, font=font_main)
        if bbox[2] - bbox[0] > (card_w - 90) and cur_line:
            lines.append(" ".join(cur_line))
            cur_line = [w]
        else:
            cur_line.append(w)
    if cur_line:
        lines.append(" ".join(cur_line))

    # Render lines
    y_offset = 32
    for line in lines[:2]:
        x_offset = 45
        line_words = line.split()
        for w in line_words:
            is_accent = w.startswith("*") or w.endswith("*") or ("*" in w)
            clean_word = w.replace("*", "")
            color = (255, 59, 59) if is_accent else (255, 255, 255)

            draw.text((x_offset, y_offset), clean_word, font=font_main, fill=color)
            w_bbox = draw.textbbox((0, 0), clean_word + " ", font=font_main)
            x_offset += (w_bbox[2] - w_bbox[0])

        y_offset += 54

    # Bottom badge / channel tag
    badge_text = f"🔥 {creator_tag} | GTA 6"
    draw.text((50, y_offset + 14), badge_text, font=font_tag, fill=(240, 240, 80))

    img.save(str(output_path), "PNG")
    return output_path


def verify_clip_with_ffprobe(clip_path: Path) -> tuple[bool, str, dict]:
    """Hard Python Verification via ffprobe (do not guess):

    Asserts output MP4 exists, is non-empty, has 9:16 vertical video (1080x1920),
    audio stream, and duration between 10s and 59s.
    """
    if not clip_path.exists() or clip_path.stat().st_size < 10240:
        sz = clip_path.stat().st_size if clip_path.exists() else 0
        return False, f"File missing or empty ({sz} bytes)", {}

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=width,height,codec_type,codec_name:format=duration,size",
        "-of",
        "json",
        str(clip_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return False, f"ffprobe execution failed: {proc.stderr[:200]}", {}

    try:
        data = json.loads(proc.stdout)
    except Exception as e:
        return False, f"ffprobe JSON parse error: {e}", {}

    streams = data.get("streams", [])
    format_info = data.get("format", {})

    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    if not video_streams:
        return False, "No video stream detected", {}
    if not audio_streams:
        return False, "No audio stream detected", {}

    v_stream = video_streams[0]
    w = int(v_stream.get("width") or 0)
    h = int(v_stream.get("height") or 0)

    if w != 1080 or h != 1920:
        return False, f"Invalid resolution {w}x{h} (expected 1080x1920 9:16)", {"width": w, "height": h}

    duration = float(format_info.get("duration") or 0)
    if duration < 10.0:
        return False, f"Clip too short ({duration:.1f}s < 10s minimum)", {"duration": duration}
    if duration > 59.9:
        return False, f"Clip too long for Shorts/Reels ({duration:.1f}s > 59s maximum)", {"duration": duration}

    details = {
        "width": w,
        "height": h,
        "duration": round(duration, 2),
        "video_codec": v_stream.get("codec_name"),
        "audio_codec": audio_streams[0].get("codec_name"),
        "size_mb": round(clip_path.stat().st_size / (1024 * 1024), 2),
    }
    return True, "OK", details


def render_vertical_clip(
    segment_path: Path,
    hook_text: str,
    clip_id: int,
    watermark_path: str = None,
    creator_tag: str = "@Creator",
    max_retries: int = 1,
) -> tuple[Path, Path, dict]:
    """Renders a 9:16 vertical 1080x1920 MP4 clip via viral_enhancer, extracts thumbnail, and verifies with ffprobe."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    clip_output_path = OUTPUT_DIR / f"clip_{clip_id}.mp4"
    thumb_output_path = OUTPUT_DIR / f"thumb_{clip_id}.jpg"

    # Quick skip if already rendered and verified
    valid, _, details = verify_clip_with_ffprobe(clip_output_path)
    if valid and thumb_output_path.exists() and thumb_output_path.stat().st_size > 1024:
        print(f"[Editor] Clip #{clip_id} already rendered and verified: {details['width']}x{details['height']} | {details['duration']}s | {details['size_mb']}MB")
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
            print(f"[Editor] Enhancement attempt {attempt+1} failed: {e}")
            if attempt == max_retries:
                raise
