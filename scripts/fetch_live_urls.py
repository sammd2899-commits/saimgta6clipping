"""Whop Submission Helper — Live Post URL Fetcher & Submission Tracker.

Polls the Zernio API v1 to retrieve newly published live Instagram Reel & YouTube Short URLs
for scheduled posts, tracks whop_submitted status in logs/published_clips.json,
and prints a clean copy-paste block of ONLY unsubmitted live clips.
"""

import argparse
import csv
import datetime
import json
import os
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import PUBLISHED_CSV, PUBLISHED_JSON, load_active_campaign
from zernio_client import ZernioClient


def sync_csv_from_json(records: list):
    with open(PUBLISHED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "clip_id", "campaign_name", "source_url", "start_time",
            "end_time", "title", "instagram_url", "youtube_url",
            "post_id", "scheduled_for", "published_at", "whop_submitted"
        ])
        for r in records:
            writer.writerow([
                r.get("clip_id"),
                r.get("campaign_name"),
                r.get("source_url"),
                r.get("start_time"),
                r.get("end_time"),
                r.get("title"),
                r.get("instagram_url") or "",
                r.get("youtube_url") or "",
                r.get("post_id") or "",
                r.get("scheduled_for") or "",
                r.get("published_at") or "",
                r.get("whop_submitted", False),
            ])


def load_and_normalize_records() -> list:
    if not PUBLISHED_JSON.exists():
        return []
    try:
        with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
            records = json.load(f)
    except Exception:
        records = []

    # Ensure whop_submitted field exists
    modified = False
    for r in records:
        if "whop_submitted" not in r:
            r["whop_submitted"] = False
            modified = True

    if modified:
        with open(PUBLISHED_JSON, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        sync_csv_from_json(records)

    return records


def mark_as_whop_submitted(clip_ids: list = None) -> int:
    """Marks specified clip IDs (or all unsubmitted live clips) as whop_submitted: True."""
    records = load_and_normalize_records()
    if not records:
        print("[Whop Helper] No published records to update.")
        return 0

    count = 0
    for r in records:
        cid = r.get("clip_id")
        # If specific IDs provided
        if clip_ids:
            if cid in clip_ids and not r.get("whop_submitted"):
                r["whop_submitted"] = True
                count += 1
        else:
            # Mark all currently live unsubmitted clips
            if r.get("status") == "published" and not r.get("whop_submitted"):
                r["whop_submitted"] = True
                count += 1

    if count > 0:
        with open(PUBLISHED_JSON, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        sync_csv_from_json(records)
        print(f"\n✅ Marked {count} clip(s) as 'whop_submitted: true'.")
        print("These links will no longer appear in future live lists to keep your workflow clean.")
    else:
        print("\n[Whop Helper] No unsubmitted live clips were found to mark.")

    return count


def fetch_live_urls(show_all: bool = False, mark_now: bool = False) -> dict:
    """Queries Zernio API for scheduled posts, updates live URLs,

    and displays ONLY unsubmitted live clips ready for Whop.
    """
    records = load_and_normalize_records()
    if not records:
        print("\n[Whop Helper] No clips found in logs/published_clips.json.")
        print("Run the pipeline on a YouTube URL first to generate and schedule clips.")
        return {"newly_live": [], "scheduled": [], "already_submitted": 0}

    client = ZernioClient()
    updated = False

    print("\n[Whop Helper] Checking Zernio API for newly published posts...")

    # Query Zernio for unsubmitted clips
    for clip in records:
        if clip.get("whop_submitted") and not show_all:
            continue

        post_id = clip.get("post_id")
        if not post_id or post_id == "unknown":
            continue

        try:
            post_data = client.get_post(post_id)
            post_obj = post_data.get("post", post_data)
            status = post_obj.get("status")

            platforms = post_obj.get("platforms", [])
            for p in platforms:
                plat = p.get("platform")
                p_url = p.get("platformPostUrl") or p.get("url")
                if plat == "instagram" and p_url:
                    if clip.get("instagram_url") != p_url:
                        clip["instagram_url"] = p_url
                        updated = True
                elif plat == "youtube" and p_url:
                    if clip.get("youtube_url") != p_url:
                        clip["youtube_url"] = p_url
                        updated = True

            if status == "published" and clip.get("status") != "published":
                clip["status"] = "published"
                # Store exact publish timestamp if returned
                pub_at = post_obj.get("publishedAt") or post_obj.get("lastSuccessfulPublishAt")
                if pub_at:
                    clip["actual_published_at"] = pub_at
                updated = True

        except Exception as e:
            # Non-blocking warning
            pass

    if updated:
        with open(PUBLISHED_JSON, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
        sync_csv_from_json(records)
        print("[Whop Helper] Synced newly live URLs into logs/published_clips.json.")

    # Filter for newly live unsubmitted clips
    newly_live = [
        c for c in records
        if c.get("status") == "published"
        and not c.get("whop_submitted")
        and (c.get("instagram_url") or c.get("youtube_url"))
    ]

    scheduled = [c for c in records if c.get("status") == "scheduled"]
    already_submitted_count = sum(1 for c in records if c.get("whop_submitted"))

    campaign = load_active_campaign()
    print("\n" + "=" * 70)
    print("📋 WHOP CONTENT REWARDS — LIVE CLIPS SUBMISSION PACK")
    print(f"Active Campaign: {campaign.get('campaign_name')}")
    print("=" * 70)

    if newly_live:
        print(f"\n🎉 {len(newly_live)} NEWLY LIVE CLIP(S) READY FOR WHOP SUBMISSION:")
        print("Copy and paste these direct URLs into your Whop Content Rewards submission:\n")
        for c in newly_live:
            cid = c.get("clip_id")
            title = c.get("title", "GTA 6 Clip")
            pub_time = c.get("actual_published_at") or c.get("scheduled_for") or c.get("published_at")
            ig = c.get("instagram_url") or "[Pending / Processing in Feed]"
            yt = c.get("youtube_url") or "[Pending / Processing in Feed]"

            print(f"Clip #{cid}: {title}")
            print(f"  • Published At:   {pub_time}")
            print(f"  • Instagram Reel: {ig}")
            print(f"  • YouTube Short:  {yt}")
            print()

        if mark_now:
            mark_as_whop_submitted([c.get("clip_id") for c in newly_live])
        else:
            print("-" * 70)
            print("👉 Want to mark these clips as submitted so they don't appear in future lists?")
            print("   Say 'mark submitted' or run: python main.py --mark-submitted")
            print("-" * 70)

    else:
        print("\n⏳ No newly live unsubmitted clips yet.")
        if scheduled:
            print(f"There are {len(scheduled)} clip(s) currently scheduled in the queue.")
            next_clip = scheduled[0]
            print(f"Next clip #{next_clip.get('clip_id')} is scheduled for: {next_clip.get('scheduled_for')}")
        if already_submitted_count > 0:
            print(f"({already_submitted_count} previous clips have already been marked submitted.)")

    print("=" * 70)
    return {
        "newly_live": newly_live,
        "scheduled": scheduled,
        "already_submitted": already_submitted_count,
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch live post URLs from Zernio for Whop Content Rewards")
    parser.add_argument("--mark-submitted", action="store_true", help="Mark all newly live clips as whop_submitted: true")
    parser.add_argument("--all", action="store_true", help="Show all clips including already submitted ones")
    args = parser.parse_args()

    if args.mark_submitted:
        mark_as_whop_submitted()
    else:
        fetch_live_urls(show_all=args.all)


if __name__ == "__main__":
    main()
