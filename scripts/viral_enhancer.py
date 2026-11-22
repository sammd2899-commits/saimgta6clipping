"""Viral Video Enhancer & Universal Safe-Zone Post-Processor.

Implements the exact layout and formatting requirements from config/editing_rules.json:
- 1080x1920 (9:16 vertical), 60fps, H.264, 6 Mbps
- Audio normalized to -14 LUFS loudnorm
- 2.5s opening hook banner at y=290px (4-7 words, bold white text, dark pill / outline)
- Word-by-word dynamic ASS captions in safe zone y=1150-1320px (68px, #FFFFFF + 5px #000000, #FFE600 active word pop)
- Split screen (top 35% facecam 1080x672 / bottom 65% gameplay 1080x1248) or full-bleed blurred-fill fallback (NO black bars)
- High-contrast vertical cover frame extraction (1:1 profile grid safe)
- Hard ffprobe verification
"""

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    CONFIG_DIR,
    OUTPUT_DIR,
    TEMP_DIR,
    load_active_campaign,
)

EDITING_RULES_PATH = CONFIG_DIR / "editing_rules.json"

SYSTEM_FONTS = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
]


def load_editing_rules() -> dict:
    if not EDITING_RULES_PATH.exists():
        raise FileNotFoundError(f"Editing rules not found at {EDITING_RULES_PATH}")
    with open(EDITING_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_font(size: int = 56):
    for fp in SYSTEM_FONTS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_hook_banner_image(
    hook_text: str,
    output_path: Path,
    font_size: int = 56,
) -> Path:
    """Renders a 4-7 word bold opening hook banner with dark pill background.

    Banner is centered horizontally and positioned at y=290px (clear of top 250px dead zone).
    """
    clean_text = hook_text.replace("*", "").strip()
    words = clean_text.split()
    if len(words) > 7:
        clean_text = " ".join(words[:7])

    font = get_font(font_size)

    # Word wrapping for safe width (max 880px to leave safe margins)
    dummy_img = Image.new("RGBA", (1080, 400), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_img)

    lines = []
    current_line = []
    for w in clean_text.split():
        test_line = " ".join(current_line + [w])
        bbox = dummy_draw.textbbox((0, 0), test_line, font=font)
        line_w = bbox[2] - bbox[0]
        if line_w > 860 and current_line:
            lines.append(" ".join(current_line))
            current_line = [w]
        else:
            current_line.append(w)
    if current_line:
        lines.append(" ".join(current_line))

    # Calculate pill dimensions
    line_bboxes = [dummy_draw.textbbox((0, 0), l, font=font) for l in lines]
    max_line_w = max(b[2] - b[0] for b in line_bboxes)
    total_line_h = sum(b[3] - b[1] for b in line_bboxes) + (len(lines) - 1) * 14

    pad_x = 44
    pad_y = 22
    pill_w = min(960, max_line_w + (pad_x * 2))
    pill_h = total_line_h + (pad_y * 2)

    img = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw dark rounded pill with subtle golden border
    draw.rounded_rectangle(
        [2, 2, pill_w - 2, pill_h - 2],
        radius=24,
        fill=(12, 12, 18, 238),
        outline=(255, 230, 0, 200),
        width=3,
    )

    # Render lines centered inside the pill
    cur_y = pad_y
    for line in lines:
        l_bbox = draw.textbbox((0, 0), line, font=font)
        l_w = l_bbox[2] - l_bbox[0]
        cur_x = (pill_w - l_w) // 2

        # Draw 3px black text outline for maximum legibility
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    draw.text((cur_x + dx, cur_y + dy), line, font=font, fill=(0, 0, 0, 255))

        draw.text((cur_x, cur_y), line, font=font, fill=(255, 255, 255, 255))
        cur_y += (l_bbox[3] - l_bbox[1]) + 14

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


def format_ass_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def generate_word_level_ass(
    audio_path: Path,
    output_ass_path: Path,
    rules: dict,
    model_name: str = "base",
) -> bool:
    """Generates ASS subtitles with word-by-word #FFE600 pop in the safe zone (y = 1150-1320px)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[Viral Enhancer] faster-whisper not installed in current environment.")
        return False

    models_dir = get_models_dir()
    try:
        if os.path.exists(models_dir):
            model = WhisperModel(model_name, download_root=models_dir, local_files_only=True)
        else:
            model = WhisperModel(model_name)
    except Exception as e:
        print(f"[Viral Enhancer] Could not initialize WhisperModel: {e}")
        return False

    try:
        import wave
        import numpy as np

        with wave.open(str(audio_path), "rb") as wf:
            raw_data = wf.readframes(wf.getnframes())
            audio_arr = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

        segments, _ = model.transcribe(
            audio_arr,
            word_timestamps=True,
            language="en",
            vad_filter=True,
        )
        words_list = []
        for segment in segments:
            if segment.words:
                for w in segment.words:
                    clean_w = w.word.strip().upper()
                    if clean_w:
                        words_list.append({
                            "word": clean_w,
                            "start": w.start,
                            "end": w.end,
                        })
    except Exception as e:
        print(f"[Viral Enhancer] Whisper transcription failed: {e}")
        return False

    if not words_list:
        print("[Viral Enhancer] No spoken words detected for dynamic captions.")
        return False

    # Caption style configs from editing_rules.json
    captions_cfg = rules.get("captions", {})
    font_size = captions_cfg.get("font_size_px", 68)
    words_per_chunk = captions_cfg.get("words_per_chunk", [2, 4])
    chunk_size = words_per_chunk[0] if len(words_per_chunk) == 1 else 3

    # ASS Header
    # MarginV=650 with Alignment=2 places bottom of text at 1920 - 650 = 1270px (within 1150-1320 safe zone)
    # PrimaryColour: &H00FFFFFF (White), Outline: 5px &H00000000 (Black)
    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,Arial,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,2,60,140,650,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    # Group into chunks of 2-4 words and generate active word highlight (&H0000E6FF = #FFE600 yellow)
    i = 0
    while i < len(words_list):
        chunk = words_list[i:i + chunk_size]
        for active_idx in range(len(chunk)):
            w_active = chunk[active_idx]
            t_start = format_ass_timestamp(w_active["start"])
            t_end = format_ass_timestamp(w_active["end"])

            # Build line where only w_active is highlighted in yellow #FFE600 (&H0000E6FF&)
            line_parts = []
            for j, w in enumerate(chunk):
                if j == active_idx:
                    line_parts.append(f"{{\\c&H0000E6FF&}}{w['word']}{{\\c&H00FFFFFF&}}")
                else:
                    line_parts.append(w["word"])

            text_line = " ".join(line_parts)
            ass_lines.append(f"Dialogue: 0,{t_start},{t_end},Default,,0,0,0,,{text_line}")

        i += len(chunk)

    output_ass_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ass_lines))

    print(f"[Viral Enhancer] Generated word-level ASS captions: {output_ass_path.name} ({len(words_list)} words)")
    return True


def verify_clip_with_ffprobe(clip_path: Path) -> tuple[bool, str, dict]:
    """Hard Python Verification via ffprobe.

    Asserts:
    - 1080x1920 (9:16 vertical)
    - Video + Audio streams present
    - Duration within hard bounds (12s to 55s)
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
    if duration < 12.0:
        return False, f"Clip too short ({duration:.1f}s < 12s minimum)", {"duration": duration}
    if duration > 55.0:
        return False, f"Clip too long ({duration:.1f}s > 55s maximum)", {"duration": duration}

    details = {
        "width": w,
        "height": h,
        "duration": round(duration, 2),
        "video_codec": v_stream.get("codec_name"),
        "audio_codec": audio_streams[0].get("codec_name"),
        "size_mb": round(clip_path.stat().st_size / (1024 * 1024), 2),
    }
    return True, "OK", details


def enhance_clip(
    segment_path: Path,
    hook_text: str,
    output_clip_path: Path,
    output_thumb_path: Path,
    facecam_crop: str = None,
    watermark_path: str = None,
) -> tuple[Path, Path, dict]:
    """Processes a raw 16:9 segment into a high-retention 9:16 vertical clip according to editing_rules.json.

    - 1080x1920 @ 60fps, 6 Mbps H.264
    - Split screen (top 35% facecam / bottom 65% gameplay) or blurred-fill fallback (NO black bars)
    - Audio normalized to -14 LUFS (loudnorm) + silence trimming
    - 2.5s opening hook banner at y=290px
    - Dynamic word-pop ASS captions at y=1150-1320px
    - 1080x1920 high-contrast thumbnail
    - Hard ffprobe verification
    """
    rules = load_editing_rules()
    video_cfg = rules.get("video", {})
    hook_cfg = rules.get("hook_banner", {})

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)
    output_thumb_path.parent.mkdir(parents=True, exist_ok=True)

    clip_id_tag = output_clip_path.stem
    hook_banner_png = TEMP_DIR / f"hook_banner_{clip_id_tag}.png"
    ass_subtitles_path = TEMP_DIR / f"captions_{clip_id_tag}.ass"

    # 1. Create opening hook banner (2.5s duration, y=290px, 4-7 words)
    create_hook_banner_image(
        hook_text=hook_text,
        output_path=hook_banner_png,
        font_size=hook_cfg.get("font_size_px", 56),
    )

    # 2. Extract audio and generate word-level ASS subtitles
    temp_audio = TEMP_DIR / f"audio_{clip_id_tag}.wav"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(segment_path), "-vn", "-ac", "1", "-ar", "16000", str(temp_audio)],
        capture_output=True,
    )
    has_ass = generate_word_level_ass(temp_audio, ass_subtitles_path, rules)
    if temp_audio.exists():
        try:
            temp_audio.unlink()
        except Exception:
            pass

    # 3. Build FFmpeg Filtergraph
    # Layout Blueprint:
    # Top 35% (672px): Streamer Facecam
    # Bottom 65% (1248px): GTA 6 Gameplay
    # Fallback: blurred-fill with zero black bars
    inputs = ["-i", str(segment_path), "-i", str(hook_banner_png)]

    if watermark_path is None:
        campaign = load_active_campaign()
        watermark_path = campaign.get("watermark_path")

    watermark_file = Path(watermark_path) if watermark_path else None
    has_watermark = watermark_file and watermark_file.exists()

    watermark_idx = None
    if has_watermark:
        watermark_idx = len(inputs) // 2
        inputs.extend(["-i", str(watermark_file)])

    filter_chains = []

    if facecam_crop is None:
        facecam_crop = rules.get("layout", {}).get("facecam_crop")

    if facecam_crop:
        # Stacked split screen mode:
        # Top 35% (672px) from facecam_crop, Bottom 65% (1248px) from gameplay
        filter_chains.append(
            f"[0:v]split=2[v_face][v_game];"
            f"[v_face]crop={facecam_crop},scale=1080:672:force_original_aspect_ratio=increase,crop=1080:672[face_top];"
            f"[v_game]scale=1080:1248:force_original_aspect_ratio=increase,crop=1080:1248[game_bot];"
            f"[face_top][game_bot]vstack=inputs=2[base_layout]"
        )
    else:
        # Fallback: full bleed with blurred vertical fill (NO black bars)
        # Background: scaled & blurred to 1080x1920
        # Foreground: 16:9 centered at 1080x608
        filter_chains.append(
            "[0:v]split=2[bg_raw][fg_raw];"
            "[bg_raw]scale=120:213:force_original_aspect_ratio=increase,crop=120:213,boxblur=3:1,scale=1080:1920:flags=bicubic[bg];"
            "[fg_raw]scale=1080:-1[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[base_layout]"
        )

    # Place campaign watermark logo cleanly in upper safe zone (y=260-330px, x=810, exact 3:1 aspect ratio, 100% duration)
    if has_watermark:
        filter_chains.append(
            f";[{watermark_idx}:v]scale=210:70[logo_scaled];"
            f"[base_layout][logo_scaled]overlay=810:260[with_logo]"
        )
        current_base = "[with_logo]"
    else:
        current_base = "[base_layout]"

    # Overlay opening hook banner (y=360px when watermark active to guarantee zero overlap, else y=290px standard)
    banner_y = 360 if has_watermark else hook_cfg.get("position_y", 290)
    filter_chains.append(
        f";{current_base}[1:v]overlay=(W-w)/2:{banner_y}:enable='between(t,0,2.5)'[with_hook]"
    )
    current_v = "[with_hook]"

    # Burn in ASS dynamic word captions if available
    if has_ass and ass_subtitles_path.exists():
        try:
            ass_rel = os.path.relpath(ass_subtitles_path, Path.cwd()).replace("\\", "/")
        except Exception:
            ass_rel = str(ass_subtitles_path).replace("\\", "/")
        filter_chains.append(f";{current_v}ass={ass_rel}[with_captions]")
        current_v = "[with_captions]"

    # Audio normalization to -14 LUFS loudnorm
    lufs = video_cfg.get("audio_loudnorm_lufs", -14)
    silence_sec = video_cfg.get("trim_silence_over_sec", 0.6)
    audio_filter = f";[0:a]silenceremove=stop_periods=-1:stop_duration={silence_sec}:stop_threshold=-40dB,loudnorm=I={lufs}:TP=-1.5:LRA=11[out_a]"
    filter_chains.append(audio_filter)

    full_filter_str = "".join(filter_chains)

    # 4. Execute FFmpeg Render (60fps, 6 Mbps, 1080x1920)
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        *inputs,
        "-filter_complex",
        full_filter_str,
        "-map",
        current_v,
        "-map",
        "[out_a]",
        "-c:v",
        video_cfg.get("codec", "libx264"),
        "-b:v",
        video_cfg.get("bitrate", "6M"),
        "-maxrate",
        "6.5M",
        "-bufsize",
        "12M",
        "-r",
        str(video_cfg.get("fps", 60)),
        "-preset",
        "fast",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_clip_path),
    ]

    print(f"[Viral Enhancer] Rendering 1080x1920 @ 60fps clip to: {output_clip_path.name}...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        # Fallback without silenceremove if audio filter failed on short audio
        print(f"[Viral Enhancer] Render notice: {proc.stderr[:150]}, retrying with standard loudnorm...")
        alt_filter = full_filter_str.replace(f"silenceremove=stop_periods=-1:stop_duration={silence_sec}:stop_threshold=-40dB,", "")
        cmd[cmd.index(full_filter_str)] = alt_filter
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg rendering failed: {proc.stderr[:300]}")

    # 5. Extract High-Contrast Thumbnail (1080x1920, 1:1 safe zone)
    thumb_cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-ss",
        "2.0",
        "-i",
        str(output_clip_path),
        "-vf",
        "eq=contrast=1.15:saturation=1.20:brightness=0.02",
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_thumb_path),
    ]
    subprocess.run(thumb_cmd, capture_output=True, text=True)

    # 6. Hard ffprobe verification
    is_valid, reason, details = verify_clip_with_ffprobe(output_clip_path)
    if not is_valid:
        raise RuntimeError(f"Enhanced clip failed ffprobe verification: {reason}")

    print(f"[Viral Enhancer] SUCCESS: {details['width']}x{details['height']} | {details['duration']}s | {details['size_mb']}MB | ffprobe verified")

    # Clean up temp overlay assets
    for p in [hook_banner_png, ass_subtitles_path]:
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    return output_clip_path, output_thumb_path, details


if __name__ == "__main__":
    banner_test = TEMP_DIR / "banner_test.png"
    create_hook_banner_image("GTA 6 NPCs are actually terrifying...", banner_test)
    print("Hook banner test created:", banner_test.exists())
