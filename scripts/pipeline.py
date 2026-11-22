"""Atomic State-Machine Pipeline for GTA 6 Stream Clipping & Scheduled Auto-Posting.

Architecture:
- Stage 1: Plan & Queue Only (state/job_queue.json)
- Stage 2: Atomic One-by-One Loop (1 Clip = 1 Clean Cycle)
  1. Download targeted 1-clip window into temp/
  2. Edit 1 clip (9:16 vertical 1080x1920) + thumbnail
  3. Hard ffprobe verification (resolution, audio, 10s-59s duration)
  4. Generate metadata with continuous learning memory
  5. Hard compliance gate (auto-appends any missing campaign tags)
  6. Upload & schedule via Zernio API v1 (scheduledFor spaced by POST_INTERVAL_HOURS)
  7. Save queue state, log to published_clips, purge temp segment, print progress update
- Resume Support: Automatically skips completed clips on restart
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
    # Update published_clips.json
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

    # Update published_clips.csv
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

    print("=" * 70)
    print("GTA 6 CLIPPER — ATOMIC CHUNKED STATE-MACHINE PIPELINE")
    print(f"Active Campaign: {campaign.get('campaign_name')}")
    print(f"Target Video:    {youtube_url}")
    print(f"Post Spacing:    Every {interval_hours} hours via Zernio scheduledFor")
    print("=" * 70)

    # Stage 1: Plan & Queue Only
    queue_data = load_job_queue()
    if resume_only and queue_data.get("clips"):
        print("[Pipeline] Resuming from existing state/job_queue.json...")
    elif queue_data.get("source_url") == youtube_url and any(c.get("status") == "PENDING" for c in queue_data.get("clips", [])):
        print("[Pipeline] Detected existing queue for this URL. Resuming pending clips...")
    else:
        print("[Pipeline] Initializing Stage 1 (Plan & Queue)...")
        queue_data = plan_and_queue(youtube_url, target_count=max_clips)

    clips = queue_data.get("clips", [])
    total_clips = len(clips)
    if not clips:
        print("[Pipeline] No clips found in queue.")
        return {"success": False, "reason": "Empty queue"}

    zernio = ZernioClient()

    # Stage 2: Atomic One-by-One Loop
    print(f"\n[Pipeline] Entering Stage 2: Processing {total_clips} clips atomically...\n")

    scheduled_count = sum(1 for c in clips if c.get("status") == "SCHEDULED")
    failed_count = sum(1 for c in clips if c.get("status") == "FAILED")

    for i, clip in enumerate(clips):
        clip_id = clip["clip_id"]
        status = clip.get("status", "PENDING")

        # Skip already processed clips (Resume support)
        if status in ("SCHEDULED", "COMPLETED"):
            print(f"  [Skip] Clip {clip_id}/{total_clips} already {status}. Moving to next.")
            continue
        if status == "FAILED":
            print(f"  [Skip] Clip {clip_id}/{total_clips} previously marked FAILED. Moving to next.")
            continue

        print(f"\n▶ [Processing Clip {clip_id}/{total_clips}] Window: {clip['start_time']}s -> {clip['end_time']}s")
        segment_path = None
        clip_file = None
        thumb_file = None

        try:
            # 1. Download ONLY that 1 clip's timestamp window
            segment_path = download_segment(youtube_url, clip["start_time"], clip["end_time"], clip_id)

            # 2 & 3. Edit 1 clip + hard ffprobe verification
            clip_file, thumb_file, probe_details = render_vertical_clip(
                segment_path=segment_path,
                hook_text=clip["hook"],
                clip_id=clip_id,
                watermark_path=campaign.get("watermark_path"),
                creator_tag=campaign.get("required_channel_tag", "@Creator"),
            )

            # 4 & 5. Generate metadata with continuous learning + hard compliance gate
            meta = generate_metadata_for_clip(clip_id, clip["hook"], campaign)

            # 6. Upload & schedule via Zernio API v1
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

            # 7. Update queue state & log
            clip["status"] = "SCHEDULED"
            clip["zernio_post_id"] = schedule_res["post_id"]
            clip["scheduled_for"] = schedule_res["scheduled_for"]
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
                "post_id": schedule_res["post_id"],
                "scheduled_for": schedule_res["scheduled_for"],
                "scheduled_ist": clip.get("scheduled_ist"),
                "instagram_url": None,
                "youtube_url": None,
                "published_at": datetime.datetime.now().astimezone().isoformat(),
                "whop_submitted": False,
            }
            log_scheduled_clip(log_record)
            scheduled_count += 1

            # Print concise progress update in IST + UTC
            sched_display = clip.get("scheduled_ist") or schedule_res["scheduled_for"]
            print(f"  ✔ Clip {clip_id}/{total_clips} SCHEDULED for {sched_display}")

        except Exception as e:
            print(f"  ✖ Clip {clip_id}/{total_clips} FAILED: {e}")
            clip["status"] = "FAILED"
            clip["error"] = str(e)
            save_job_queue(queue_data)
            failed_count += 1

        finally:
            # Immediate temp cleanup for this 1 clip
            if segment_path and segment_path.exists():
                cleanup_temp_segment(segment_path)

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("🏁 ATOMIC BATCH EXECUTION COMPLETE")
    print(f"Total Clips in Queue: {total_clips}")
    print(f"Successfully Scheduled: {scheduled_count}")
    print(f"Failed: {failed_count}")
    print(f"Execution Time: {elapsed / 60:.1f} minutes")
    print("=" * 70)
    print("Run 'python scripts/fetch_live_urls.py' to view live Whop submission links as posts go live.")
    return queue_data


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <YOUTUBE_URL> [--resume]")
        sys.exit(1)
    url = sys.argv[1]
    resume = "--resume" in sys.argv
    run_pipeline(url, resume_only=resume)
