"""Video Analyzer & Stage 1 Plan-and-Queue Engine.

Discovers high-engagement moments using yt-dlp metadata, YouTube Heatmap (Most Replayed),
and moment_selector WITHOUT downloading full multi-hour VODs.
Outputs strict candidate state into state/job_queue.json for atomic processing.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
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

HOOK_TEMPLATES = [
    "Wait until you see how this GTA 6 chase ends 🚨",
    "Nobody expected THIS to happen in GTA 6 🤯",
    "This GTA 6 police chase got *COMPLETELY OUT OF HAND* 💀",
    "Rockstar definitely didn't plan for THIS GTA 6 moment 🚔",
    "Is this the *HARDEST MISSION* in GTA 6? 💥",
    "Discovered an *INSANE SECRET* location in GTA 6 🗺️",
    "The GTA 6 physics just *BROKE COMPLETELY* 😭",
    "Nobody expected this wild GTA 6 NPC reaction 🌴",
    "You won't believe this GTA 6 escape move 🏎️💨",
    "GTA 6 graphics and chaos are *NEXT LEVEL* 🔥",
]


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
        raise RuntimeError(f"yt-dlp failed to fetch info: {proc.stderr[:300]}")
    return json.loads(proc.stdout)


def get_already_clipped_ranges(source_url: str) -> list[tuple[float, float]]:
    if not PUBLISHED_JSON.exists():
        return []
    try:
        with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
            records = json.load(f)
        ranges = []
        for r in records:
            if r.get("source_url") == source_url and "start_time" in r and "end_time" in r:
                ranges.append((float(r["start_time"]), float(r["end_time"])))
        return ranges
    except Exception:
        return []


def is_overlapping(start: float, end: float, existing_ranges: list[tuple[float, float]], threshold: float = 10.0) -> bool:
    for es, ee in existing_ranges:
        overlap = max(0.0, min(end, ee) - max(start, es))
        if overlap >= threshold:
            return True
    return False


def discover_viral_moments(url: str, target_count: int = None) -> dict:
    print(f"\n[Analyzer] Fetching metadata & heatmap for: {url}")
    info = run_ytdlp_json(url)

    title = info.get("title", "GTA 6 Livestream")
    uploader = info.get("uploader") or info.get("channel", "Creator")
    duration = float(info.get("duration") or 0)
    heatmap = info.get("heatmap") or []
    video_id = info.get("id", "video")

    print(f"[Analyzer] Title: {title}")
    print(f"[Analyzer] Creator: {uploader} | Duration: {duration/60:.1f} minutes")
    print(f"[Analyzer] Heatmap data points available: {len(heatmap)}")

    campaign = load_active_campaign()
    learned_rules = load_learned_rules()
    print(f"[Analyzer] Active Campaign: {campaign.get('campaign_name')}")
    if learned_rules:
        print("[Analyzer] Applied learned rules from memory/learned_rules.md")

    # Determine desired clip count: 12 to 30 moments for long livestreams
    if target_count is None:
        if duration >= 7200:      # 2+ hours
            target_count = 20
        elif duration >= 3600:    # 1+ hours
            target_count = 15
        elif duration >= 1800:    # 30+ mins
            target_count = 8
        elif duration >= 600:     # 10+ mins
            target_count = 5
        else:
            target_count = max(2, int(duration // 60))
        target_count = min(30, max(2, target_count))

    print(f"[Analyzer] Target viral moment count to extract: {target_count}")

    already_clipped = get_already_clipped_ranges(url)
    if already_clipped:
        print(f"[Analyzer] Found {len(already_clipped)} already clipped timestamp windows. Skipping overlaps.")

    candidate_moments = select_viral_moments(
        info=info,
        target_count=target_count,
        already_clipped_ranges=already_clipped,
    )

    print(f"[Analyzer] Successfully identified {len(candidate_moments)} viral moments!")
    return {
        "url": url,
        "video_id": video_id,
        "title": title,
        "uploader": uploader,
        "duration": duration,
        "moments": candidate_moments,
    }


def plan_and_queue(url: str, target_count: int = None) -> dict:
    """Stage 1: Analyzes video, selects moments, assigns awake IST slots, and writes state/job_queue.json."""
    # 0. Quick pre-planning Viral Learning Engine refresh
    try:
        from viral_learner import ViralLearner
        print("[Stage 1] Refreshing Viral Learning Engine weights before planning...")
        ViralLearner().run_learning_cycle()
    except Exception as e:
        print(f"[Stage 1] Notice: Viral learner check bypassed ({e})")

    analysis = discover_viral_moments(url, target_count=target_count)
    moments = analysis.get("moments", [])

    # Assign awake IST slots (Asia/Kolkata -> UTC)
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
    print(f"[Stage 1] Plan created: {len(moments)} clips saved to state/job_queue.json with status=PENDING.")
    return queue_data


if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    q = plan_and_queue(test_url, target_count=4)
    print("Queue initialized with", len(q["clips"]), "clips.")
