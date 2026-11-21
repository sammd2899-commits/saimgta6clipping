"""Live Post URL Fetcher for Whop Content Rewards Submission.

Queries Zernio API for post publication status and extracts live Instagram/YouTube URLs.
Tracks whop_submitted state in logs/published_clips.json and logs/published_clips.csv.
"""

import csv
import json
import os
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    PUBLISHED_CSV,
    PUBLISHED_JSON,
    get_zernio_api_key,
)
from zernio_client import ZernioClient


def load_published_records() -> list[dict]:
    if not PUBLISHED_JSON.exists():
        return []
    try:
        with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_published_records(records: list[dict]):
    PUBLISHED_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(PUBLISHED_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

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


def fetch_live_urls() -> list[dict]:
    records = load_published_records()
    if not records:
        print("[Live URLs] No published or scheduled clips found in logs/published_clips.json")
        return []

    try:
        client = ZernioClient()
    except Exception as e:
        print(f"[Live URLs] Zernio client unavailable: {e}")
        return records

    updated = False
    for r in records:
        post_id = r.get("post_id")
        if not post_id or post_id.startswith("mock_") or post_id.startswith("local_"):
            continue

        if not r.get("instagram_url") or not r.get("youtube_url"):
            try:
                status_data = client.get_post_status(post_id)
                post = status_data.get("post") or status_data
                platforms = post.get("platforms") or {}

                ig_url = platforms.get("instagram", {}).get("postUrl") or platforms.get("instagram", {}).get("url")
                yt_url = platforms.get("youtube", {}).get("postUrl") or platforms.get("youtube", {}).get("url")

                if ig_url and not r.get("instagram_url"):
                    r["instagram_url"] = ig_url
                    updated = True
                if yt_url and not r.get("youtube_url"):
                    r["youtube_url"] = yt_url
                    updated = True
            except Exception:
                pass

    if updated:
        save_published_records(records)

    print("=" * 80)
    print("LIVE POST URLS FOR WHOP CONTENT REWARDS")
    print("=" * 80)
    for r in records:
        cid = r.get("clip_id")
        ig = r.get("instagram_url") or "Pending publication"
        yt = r.get("youtube_url") or "Pending publication"
        whop = "SUBMITTED" if r.get("whop_submitted") else "READY TO SUBMIT"
        print(f"Clip #{cid} [{whop}]:")
        print(f"  • Instagram Reel:  {ig}")
        print(f"  • YouTube Short:   {yt}")
    print("=" * 80)
    return records


def mark_as_whop_submitted(clip_ids: list[int] = None):
    records = load_published_records()
    for r in records:
        if clip_ids is None or r.get("clip_id") in clip_ids:
            if r.get("instagram_url") or r.get("youtube_url"):
                r["whop_submitted"] = True
    save_published_records(records)
    print(f"[Whop Tracker] Marked clips as submitted in logs/published_clips.json")


if __name__ == "__main__":
    fetch_live_urls()
