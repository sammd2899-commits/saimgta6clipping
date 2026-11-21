"""SaimGTA6Clipping — High-Retention GTA 6 Stream Clipping & Scheduled Auto-Posting.

Main CLI Entry Point.
"""

import argparse
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analyzer import plan_and_queue
from bootstrap import run_bootstrap
from campaign_manager import show_active_campaign, update_campaign_from_dict
from config_manager import (
    append_learned_rule,
    load_active_campaign,
    load_job_queue,
    load_learned_rules,
    load_zernio_accounts,
)
from fetch_live_urls import fetch_live_urls, mark_as_whop_submitted
from pipeline import run_pipeline
from scheduler import get_next_available_slots, load_schedule_config, print_schedule_table
from zernio_client import ZernioClient


def show_queue():
    queue = load_job_queue()
    clips = queue.get("clips", [])
    print("=" * 70)
    print("JOB QUEUE STATUS (state/job_queue.json)")
    print("=" * 70)
    print(f"Source URL:   {queue.get('source_url')}")
    print(f"Video Title:  {queue.get('video_title')}")
    print(f"Total Clips:  {len(clips)}")
    print(f"Last Updated: {queue.get('last_updated')}")
    print("-" * 70)

    pending = [c for c in clips if c.get("status") == "PENDING"]
    scheduled = [c for c in clips if c.get("status") == "SCHEDULED"]
    failed = [c for c in clips if c.get("status") == "FAILED"]

    print(f"Summary: {len(scheduled)} Scheduled | {len(pending)} Pending | {len(failed)} Failed\n")
    for c in clips:
        st = c.get("status", "PENDING")
        cid = c.get("clip_id")
        window = f"{c.get('start_time')}s-{c.get('end_time')}s"
        sched = f" -> Sched: {c.get('scheduled_for')}" if c.get("scheduled_for") else ""
        print(f"  [{st:<9}] Clip #{cid:<2} ({window}) | Hook: {c.get('hook')[:40]}...{sched}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="SaimGTA6Clipping — High-Retention GTA 6 Stream Clipper & Multi-Platform Auto-Poster",
    )
    parser.add_argument("url", nargs="?", help="YouTube video or livestream URL to clip & post")
    parser.add_argument("--bootstrap", action="store_true", help="Run automated environment and tool setup")
    parser.add_argument("--resume", action="store_true", help="Resume pending clips from state/job_queue.json")
    parser.add_argument("--plan-only", action="store_true", help="Run Stage 1 only (create job_queue.json without downloading)")
    parser.add_argument("--max-clips", type=int, default=None, help="Maximum number of clips to extract")
    parser.add_argument("--fetch-urls", action="store_true", help="Fetch live post URLs from Zernio for Whop submission")
    parser.add_argument("--mark-submitted", action="store_true", help="Mark newly live clips as whop_submitted: true")
    parser.add_argument("--show-queue", action="store_true", help="Display current job queue status")
    parser.add_argument("--learn", type=str, help="Append a learned rule/preference to memory/learned_rules.md")
    parser.add_argument("--show-rules", action="store_true", help="Display learned rules memory")
    parser.add_argument("--verify-zernio", action="store_true", help="Test Zernio API connection and refresh account cache")
    parser.add_argument("--show-campaign", action="store_true", help="Display current active campaign rules")
    parser.add_argument("--show-schedule", action="store_true", help="Display current awake schedule & next slots")

    args = parser.parse_args()

    if args.bootstrap:
        run_bootstrap()
        return

    if args.verify_zernio:
        client = ZernioClient()
        accs = client.discover_and_save_accounts()
        print("\n✅ Zernio verification successful. Accounts synced.")
        return

    if args.show_campaign:
        show_active_campaign()
        return

    if args.show_schedule:
        cfg = load_schedule_config()
        print(f"Timezone: {cfg.get('timezone')} (UTC offset: +{cfg.get('utc_offset_hours')}h)")
        slots = get_next_available_slots(10)
        print_schedule_table(slots)
        return

    if args.show_rules:
        print(load_learned_rules())
        return

    if args.learn:
        append_learned_rule("User Directive", args.learn)
        print(f"Logged new rule to memory/learned_rules.md: {args.learn}")
        return

    if args.show_queue:
        show_queue()
        return

    if args.fetch_urls:
        fetch_live_urls()
        return

    if args.mark_submitted:
        mark_as_whop_submitted()
        return

    if args.url:
        if args.plan_only:
            plan_and_queue(args.url, target_count=args.max_clips)
        else:
            run_pipeline(args.url, max_clips=args.max_clips, resume_only=args.resume)
        return

    if args.resume:
        run_pipeline(youtube_url=None, resume_only=True)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
