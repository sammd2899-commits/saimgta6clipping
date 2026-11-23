"""Targeted Segment Downloader.

Downloads ONLY the selected timestamp windows into temp/
using yt-dlp --download-sections, avoiding multi-hour VOD downloads.
"""

import os
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import TEMP_DIR, get_ytdlp_cmd


def _run_cmd_with_ssl_fallback(base_cmd: list, output_path: Path, ytdlp_cmd_len: int) -> subprocess.CompletedProcess:
    """Runs yt-dlp with standard SSL verification first, and ONLY retries with

    --no-check-certificates if CERTIFICATE_VERIFY_FAILED occurs.
    """
    proc = subprocess.run(base_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
        err_msg = (proc.stderr or "") + (proc.stdout or "")
        if "certificate_verify_failed" in err_msg.lower() or "certificate verify failed" in err_msg.lower():
            print("[Downloader] Notice: Local SSL inspection detected. Retrying segment download with --no-check-certificates fallback...")
            retry_cmd = list(base_cmd)
            retry_cmd.insert(ytdlp_cmd_len, "--no-check-certificates")
            proc = subprocess.run(retry_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc


def download_segment(url: str, start_time: float, end_time: float, clip_id: int) -> Path:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_filename = f"segment_{clip_id}_{int(start_time)}_{int(end_time)}.mp4"
    output_path = TEMP_DIR / output_filename

    if output_path.exists() and output_path.stat().st_size > 1024:
        return output_path

    section_arg = f"*{start_time:.2f}-{end_time:.2f}"
    ytdlp_cmd = get_ytdlp_cmd()

    # Primary command: Standard SSL verification by default (100% verified)
    cmd = [
        *ytdlp_cmd,
        "--js-runtimes",
        "node",
        "--extractor-args",
        "youtube:player_client=android,web",
        "--download-sections",
        section_arg,
        "-f",
        "bestvideo[vcodec^=avc1][height<=1080]+bestaudio[ext=m4a]/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "--no-playlist",
        "--force-overwrites",
        "-o",
        str(output_path),
        url,
    ]

    proc = _run_cmd_with_ssl_fallback(cmd, output_path, len(ytdlp_cmd))
    if proc.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
        # Fallback command: standard SSL verification first, SSL fallback if needed
        cmd_fallback = [
            *ytdlp_cmd,
            "--js-runtimes",
            "node",
            "--extractor-args",
            "youtube:player_client=android,web",
            "--download-sections",
            section_arg,
            "-f",
            "best/18",
            "--merge-output-format",
            "mp4",
            "--no-playlist",
            "--force-overwrites",
            "-o",
            str(output_path),
            url,
        ]
        proc2 = _run_cmd_with_ssl_fallback(cmd_fallback, output_path, len(ytdlp_cmd))
        if proc2.returncode != 0 or not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Failed to download segment #{clip_id}: {proc.stderr[:300]}")

    return output_path


def cleanup_temp_segment(file_path: Path):
    try:
        if file_path and file_path.exists():
            file_path.unlink()
    except Exception:
        pass
