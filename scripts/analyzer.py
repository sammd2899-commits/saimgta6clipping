"""Video Analyzer & Stage 1 Plan-and-Queue Engine.

Discovers high-engagement moments using yt-dlp metadata, YouTube Heatmap (Most Replayed),
and moment_selector WITHOUT downloading full multi-hour VODs.
Outputs strict candidate state into state/job_queue.json for atomic processing.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    LOGS_DIR,
    PUBLISHED_JSON,
    QUEUE_PATH,
    TEMP_DIR,
    get_ytdlp_cmd,
    load_active_campaign,
    load_learned_rules,
    save_job_queue,
)
from moment_selector import select_viral_moments
from scheduler import get_next_available_slots, print_schedule_table


def run_ytdlp_json(url: str) -> dict:
    ytdlp_cmd = get_ytdlp_cmd()
    cmd = [
        *ytdlp_cmd,
        "--js-runtimes",
        "node",
        "--dump-single-json",
        "--skip-download",
        "--no-playlist",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp failed to fetch video metadata: {proc.stderr[:300]}")
    return json.loads(proc.stdout)


def get_already_clipped_ranges(url: str) -> list[tuple[float, float]]:
    if not PUBLISHED_JSON.exists():
        return []
    try:
        with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            ranges = []
            for item in data:
                if item.get("source_url") == url:
                    s = float(item.get("start_time", 0))
                    e = float(item.get("end_time", 0))
                    if e > s:
                        ranges.append((s, e))
            return ranges
    except Exception:
        return []


def discover_viral_moments(url: str, target_count: int = None) -> dict:
    info = run_ytdlp_json(url)

    title = info.get("title", "GTA 6 Livestream")
    uploader = info.get("uploader") or info.get("channel", "Creator")
    duration = float(info.get("duration") or 0)
    video_id = info.get("id", "video")

    already_clipped = get_already_clipped_ranges(url)
    candidate_moments = select_viral_moments(
        info=info,
        target_count=target_count,
        already_clipped_ranges=already_clipped,
    )

    return {
        "url": url,
        "video_id": video_id,
        "title": title,
        "uploader": uploader,
        "duration": duration,
        "moments": candidate_moments,
    }


def plan_and_queue(url: str, target_count: int = None) -> dict:
    analysis = discover_viral_moments(url, target_count=target_count)
    moments = analysis.get("moments", [])

    if moments:
        slots = get_next_available_slots(len(moments))
        for idx, m in enumerate(moments):
            if idx < len(slots):
                m["scheduled_for"] = slots[idx]["scheduled_for_utc"]
                m["scheduled_ist"] = slots[idx]["datetime_ist_display"]
        print_schedule_table(slots)

    queue_data = {
        "source_url": url,
        "video_title": analysis.get("title"),
        "created_at": analysis.get("uploader"),
        "total_clips": len(moments),
        "clips": moments,
    }
    save_job_queue(queue_data)
    return queue_data
