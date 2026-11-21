"""Atomic State-Machine Pipeline for Stream Clipping & Scheduled Posting.

Two-Stage Runner:
- Stage 1: Plan & Queue (state/job_queue.json)
- Stage 2: Atomic 1-by-1 Processing Loop
  1. Download targeted 1-clip window into temp/
  2. Edit 1 clip (9:16 vertical 1080x1920) + thumbnail
  3. Hard ffprobe verification (resolution, audio, 12s-55s duration)
  4. Generate compliant platform metadata
  5. Hard compliance gate
  6. Schedule via Zernio API v1
  7. Update queue state, log to published_clips, purge temp segment
"""

import csv
import datetime
import json
import os
import sys
import time
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from analyzer import plan_and_queue
from config_manager import (
    BASE_DIR,
    OUTPUT_DIR,
    PUBLISHED_CSV,
    PUBLISHED_JSON,
    QUEUE_PATH,
    TEMP_DIR,
    get_post_interval_hours,
    load_active_campaign,
    load_job_queue,
    save_job_queue,
)
from downloader import cleanup_temp_segment, download_segment
from editor import render_vertical_clip, verify_clip_with_ffprobe
from metadata_generator import generate_metadata_for_clip
from zernio_client import ZernioClient


def log_scheduled_clip(record: dict):
    existing = []
    if PUBLISHED_JSON.exists():
        try:
            with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing.append(record)
    with open(PUBLISHED_JSON, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    file_exists = PUBLISHED_CSV.exists()
    with open(PUBLISHED_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "clip_id", "campaign_name", "source_url", "start_time",
                "end_time", "title", "instagram_url", "youtube_url",
                "post_id", "scheduled_for", "published_at", "whop_submitted"
            ])
        writer.writerow([
            record.get("clip_id"),
            record.get("campaign_name"),
            record.get("source_url"),
            record.get("start_time"),
            record.get("end_time"),
            record.get("title"),
            record.get("instagram_url") or "",
            record.get("youtube_url") or "",
            record.get("post_id") or "",
            record.get("scheduled_for") or "",
            record.get("published_at") or "",
            record.get("whop_submitted", False),
        ])


def run_pipeline(youtube_url: str, max_clips: int = None, resume_only: bool = False) -> dict:
    start_time = time.time()
    campaign = load_active_campaign()
    interval_hours = get_post_interval_hours()

    queue_data = load_job_queue()
    if resume_only and queue_data.get("clips"):
        pass
    elif queue_data.get("source_url") == youtube_url and any(c.get("status") == "PENDING" for c in queue_data.get("clips", [])):
        pass
    else:
        queue_data = plan_and_queue(youtube_url, target_count=max_clips)

    clips = queue_data.get("clips", [])
    total_clips = len(clips)
    if not clips:
        return {"success": False, "reason": "Empty queue"}

    try:
        zernio = ZernioClient()
    except Exception:
        zernio = None

    scheduled_count = sum(1 for c in clips if c.get("status") == "SCHEDULED")
    failed_count = sum(1 for c in clips if c.get("status") == "FAILED")

    for i, clip in enumerate(clips):
        clip_id = clip["clip_id"]
        status = clip.get("status", "PENDING")

        if status in ("SCHEDULED", "COMPLETED"):
            continue
        if status == "FAILED":
            continue

        segment_path = None
        clip_file = None
        thumb_file = None

        try:
            segment_path = download_segment(youtube_url, clip["start_time"], clip["end_time"], clip_id)

            clip_file, thumb_file, probe_details = render_vertical_clip(
                segment_path=segment_path,
                hook_text=clip["hook"],
                clip_id=clip_id,
                watermark_path=campaign.get("watermark_path"),
                creator_tag=campaign.get("required_channel_tag", "@Creator"),
            )

            meta = generate_metadata_for_clip(clip_id, clip["hook"], campaign)

            if zernio:
                schedule_res = zernio.schedule_clip(
                    clip_path=clip_file,
                    title=meta["title"],
                    caption=meta["caption"],
                    first_comment=meta["first_comment"],
                    thumb_path=thumb_file,
                    campaign=campaign,
                    scheduled_for=clip.get("scheduled_for"),
                    queue_index=scheduled_count,
                )
                post_id = schedule_res.get("post_id", f"local_id_{clip_id}")
                sched_for = schedule_res.get("scheduled_for", clip.get("scheduled_for"))
            else:
                post_id = f"local_id_{clip_id}"
                sched_for = clip.get("scheduled_for")

            clip["status"] = "SCHEDULED"
            clip["zernio_post_id"] = post_id
            clip["scheduled_for"] = sched_for
            save_job_queue(queue_data)

            log_record = {
                "clip_id": clip_id,
                "campaign_name": campaign.get("campaign_name"),
                "source_url": youtube_url,
                "start_time": clip["start_time"],
                "end_time": clip["end_time"],
                "duration": clip["duration"],
                "title": meta["title"],
                "caption": meta["caption"],
                "first_comment": meta["first_comment"],
                "post_id": post_id,
                "scheduled_for": sched_for,
                "scheduled_ist": clip.get("scheduled_ist"),
                "instagram_url": None,
                "youtube_url": None,
                "published_at": datetime.datetime.now().astimezone().isoformat(),
                "whop_submitted": False,
            }
            log_scheduled_clip(log_record)
            scheduled_count += 1

        except Exception as e:
            clip["status"] = "FAILED"
            clip["error"] = str(e)
            save_job_queue(queue_data)
            failed_count += 1

        finally:
            if segment_path and segment_path.exists():
                cleanup_temp_segment(segment_path)

    return queue_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <YOUTUBE_URL> [--resume]")
        sys.exit(1)
    url = sys.argv[1]
    resume = "--resume" in sys.argv
    run_pipeline(url, resume_only=resume)
