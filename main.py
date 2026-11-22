"""SaimGTA6Clipping — High-Retention GTA 6 Stream Clipping & Scheduled Auto-Posting Studio.

Master CLI Entry Point for Autonomous & Chat-Directed Execution (v3.0).

Features:
- Stage 1: Plan & Queue (state/job_queue.json) with Deterministic Viral Auto-Ranking
- Stage 2: Atomic 1-by-1 Processing Loop with Hard ffprobe & Safe-Zone Verification
- Campaign Preset Switcher (config/presets/ + "switch campaign")
- Auto-VOD Streamer Watcher (config/watched_streamers.json + "check new streams")
- Fixed Awake IST Scheduling Engine (Asia/Kolkata -> ISO 8601 UTC)
- Whop Content Rewards Submission Helper (live URL tracking & "mark submitted")
- Closed-Loop Viral Learning Engine & Winner Clone Blueprint (--learn-analytics, --clone-winners)
- Pre-Flight Health Check Diagnostic Engine (scripts/health_check.py)
"""

import argparse
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from analyzer import plan_and_queue
from campaign_manager import (
    list_campaign_presets,
    print_presets_table,
    show_active_campaign,
    switch_campaign_preset,
    update_campaign_from_dict,
)
from config_manager import (
    append_learned_rule,
    load_active_campaign,
    load_job_queue,
    load_learned_rules,
    load_zernio_accounts,
)
from fetch_live_urls import fetch_live_urls, mark_as_whop_submitted
from health_check import run_health_check
from pipeline import run_pipeline
from scheduler import (
    get_next_available_slots,
    load_schedule_config,
    print_schedule_table,
    update_schedule_interactively,
)
from vod_watcher import check_new_streams, list_watched_streamers
from zernio_client import ZernioClient


def show_queue():
    queue = load_job_queue()
    clips = queue.get("clips", [])
    print("=" * 75)
    print("JOB QUEUE STATUS (state/job_queue.json)")
    print("=" * 75)
    print(f"Source URL:   {queue.get('source_url')}")
    print(f"Video Title:  {queue.get('video_title')}")
    print(f"Total Clips:  {len(clips)}")
    print(f"Last Updated: {queue.get('last_updated')}")
    print("-" * 75)

    pending = [c for c in clips if c.get("status") == "PENDING"]
    scheduled = [c for c in clips if c.get("status") == "SCHEDULED"]
    failed = [c for c in clips if c.get("status") == "FAILED"]

    print(f"Summary: {len(scheduled)} Scheduled | {len(pending)} Pending | {len(failed)} Failed\n")
    for c in clips:
        st = c.get("status", "PENDING")
        cid = c.get("clip_id")
        score = f" [Score: {c.get('predicted_viral_score', 0):.1f}]" if "predicted_viral_score" in c else ""
        ab = " [A/B Test]" if c.get("ab_test") else ""
        window = f"{c.get('start_time')}s-{c.get('end_time')}s"
        sched = f" -> Sched: {c.get('scheduled_for')}" if c.get("scheduled_for") else ""
        print(f"  [{st:<9}] Clip #{cid:<2} ({window}){score}{ab} | Hook: {c.get('hook')[:35]}...{sched}")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(
        description="SaimGTA6Clipping — Autonomous GTA 6 Stream Clipping & Scheduled Auto-Posting Studio",
    )
    parser.add_argument("url", nargs="?", help="YouTube video, livestream URL, or stream # to clip & post")
    parser.add_argument("--resume", action="store_true", help="Resume pending clips from state/job_queue.json")
    parser.add_argument("--plan-only", action="store_true", help="Run Stage 1 only (create job_queue.json without downloading)")
    parser.add_argument("--max-clips", type=int, default=None, help="Maximum number of clips to extract (12-30 default)")
    parser.add_argument("--fetch-urls", action="store_true", help="Fetch live post URLs from Zernio for Whop submission")
    parser.add_argument("--mark-submitted", action="store_true", help="Mark newly live clips as whop_submitted: true")
    parser.add_argument("--show-queue", action="store_true", help="Display current job queue status")
    parser.add_argument("--learn", type=str, help="Append a learned rule/preference to memory/learned_rules.md")
    parser.add_argument("--show-rules", action="store_true", help="Display learned rules memory")
    parser.add_argument("--learn-analytics", action="store_true", help="Run closed-loop Viral Learning Engine on live Zernio metrics")
    parser.add_argument("--clone-winners", action="store_true", help="Display top winning clips and Viral DNA clone blueprint")
    parser.add_argument("--verify-zernio", action="store_true", help="Test Zernio API connection and refresh account cache")
    parser.add_argument("--show-campaign", action="store_true", help="Display current active campaign rules")
    parser.add_argument("--update-campaign", action="store_true", help="Update active campaign brief and save as preset")
    parser.add_argument("--switch-campaign", nargs="?", const="__LIST__", help="Switch active campaign to a preset (by name, slug, or index)")
    parser.add_argument("--list-presets", action="store_true", help="List all saved campaign presets in config/presets/")
    parser.add_argument("--check-streams", action="store_true", help="Scan watched streamer channels for fresh unclipped VODs")
    parser.add_argument("--list-streamers", action="store_true", help="List approved streamer channels configured to watch")
    parser.add_argument("--health-check", action="store_true", help="Run pre-flight system health check and diagnostics")
    parser.add_argument("--show-schedule", action="store_true", help="Display current IST awake schedule & next slots")
    parser.add_argument("--update-schedule", action="store_true", help="Update IST slots or daily cap")

    args = parser.parse_args()

    if args.health_check:
        run_health_check()
        return

    if args.check_streams:
        check_new_streams()
        return

    if args.list_streamers:
        list_watched_streamers()
        return

    if args.list_presets or args.switch_campaign == "__LIST__":
        print_presets_table()
        return

    if args.switch_campaign and args.switch_campaign != "__LIST__":
        switch_campaign_preset(args.switch_campaign)
        return

    if args.verify_zernio:
        client = ZernioClient()
        accs = client.discover_and_save_accounts()
        print("\n✅ Zernio verification successful. Connected accounts are active and ready for posting.")
        return

    if args.show_campaign:
        show_active_campaign()
        return

    if args.show_schedule:
        cfg = load_schedule_config()
        print("=" * 80)
        print("FIXED AWAKE-HOUR SCHEDULE CONFIG (config/schedule_config.json)")
        print("=" * 80)
        print(f"Timezone:         {cfg.get('timezone')} (UTC+05:30)")
        print(f"Daily Slots (IST): {', '.join(cfg.get('daily_slots_ist', []))}")
        print(f"Daily Cap:        {cfg.get('max_clips_per_day')} clips/day")
        print(f"Notes:            {cfg.get('notes')}")
        slots = get_next_available_slots(10)
        print_schedule_table(slots)
        return

    if args.update_schedule:
        print("\n=== UPDATE SCHEDULE ===")
        print("Provide new slots or daily cap via scheduler.update_schedule_interactively().")
        return

    if args.update_campaign:
        print("\n=== UPDATE CAMPAIGN BRIEF ===")
        print("Provide updated rules or paste new brief via campaign_manager.update_campaign_from_dict().")
        return

    if args.show_queue:
        show_queue()
        return

    if args.show_rules:
        rules = load_learned_rules()
        print("=" * 75)
        print("CONTINUOUS LEARNING MEMORY (memory/learned_rules.md)")
        print("=" * 75)
        print(rules)
        print("=" * 75)
        return

    if args.learn_analytics:
        from viral_learner import main as run_learner
        run_learner()
        return

    if args.clone_winners:
        from viral_learner import ViralLearner
        print(ViralLearner().clone_winners_report())
        return

    if args.learn:
        append_learned_rule("User Directive", args.learn)
        print("✅ Rule updated and locked into continuous learning memory.")
        return

    if args.fetch_urls:
        fetch_live_urls()
        return

    if args.mark_submitted:
        mark_as_whop_submitted()
        return

    if args.plan_only:
        if not args.url:
            print("Error: --plan-only requires a YouTube URL.")
            sys.exit(1)
        plan_and_queue(args.url, target_count=args.max_clips)
        show_queue()
        return

    if args.resume:
        queue = load_job_queue()
        if not queue.get("source_url"):
            print("Error: No existing job queue found to resume.")
            sys.exit(1)
        run_pipeline(queue["source_url"], resume_only=True)
        return

    if args.url:
        # Check if user typed "clip #1" or "#1" or "1"
        target_url = args.url
        clean_choice = target_url.lower().replace("clip", "").replace("#", "").strip()
        if clean_choice.isdigit():
            # Match stream choice from vod_watcher
            streams = check_new_streams(verbose=False)
            idx = int(clean_choice)
            if 1 <= idx <= len(streams):
                target_url = streams[idx - 1]["url"]
                print(f"Selected stream #{idx}: {streams[idx-1]['title']} ({target_url})")
            else:
                print(f"Error: Stream index #{clean_choice} out of range (Found {len(streams)} fresh streams).")
                sys.exit(1)

        run_pipeline(target_url, max_clips=args.max_clips)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
