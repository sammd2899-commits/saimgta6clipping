"""Auto-VOD & Streamer Watcher Engine.

Scans approved streamer channels for fresh GTA 6 livestreams and VODs:
1. Uses lightweight 'yt-dlp --flat-playlist --dump-json' (metadata only — NEVER downloads full videos).
2. Filters out streams already processed in logs/published_clips.json or state/job_queue.json.
3. Ranks fresh streams by view velocity, publish recency, and learned streamer_source_weights.
4. Outputs a clean numbered list for instant 1-click or chat-driven clipping ("clip #1").
"""

import argparse
import datetime
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
    BASE_DIR,
    CONFIG_DIR,
    PUBLISHED_JSON,
    QUEUE_PATH,
    WATCHED_STREAMERS_PATH,
    get_ytdlp_cmd,
    load_viral_dna_weights,
)

EXAMPLE_STREAMERS_PATH = CONFIG_DIR / "watched_streamers.example.json"


def load_watched_streamers_config() -> dict:
    if WATCHED_STREAMERS_PATH.exists():
        try:
            with open(WATCHED_STREAMERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    if EXAMPLE_STREAMERS_PATH.exists():
        try:
            with open(EXAMPLE_STREAMERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "description": "Approved streamer channel URLs",
        "streamers": [],
        "scan_settings": {"max_streams_per_channel": 3, "max_vod_age_days": 7},
    }


def save_watched_streamers_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(WATCHED_STREAMERS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_already_processed_ids() -> set[str]:
    """Collects all video IDs and URLs already scheduled, published, or queued."""
    processed = set()

    # From published_clips.json
    if PUBLISHED_JSON.exists():
        try:
            with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
                pubs = json.load(f)
                for p in pubs:
                    src = p.get("source_url") or ""
                    if src:
                        processed.add(src)
                        # Extract 11-char video id
                        m = re.search(r"(?:v=|\/live\/|youtu\.be\/)([a-zA-Z0-9_-]{11})", src)
                        if m:
                            processed.add(m.group(1))
        except Exception:
            pass

    # From job_queue.json
    if QUEUE_PATH.exists():
        try:
            with open(QUEUE_PATH, "r", encoding="utf-8") as f:
                q = json.load(f)
                src = q.get("source_url") or ""
                if src:
                    processed.add(src)
                    m = re.search(r"(?:v=|\/live\/|youtu\.be\/)([a-zA-Z0-9_-]{11})", src)
                    if m:
                        processed.add(m.group(1))
        except Exception:
            pass

    return processed


def fetch_channel_recent_streams(channel_url: str, max_items: int = 3) -> list[dict]:
    """Queries yt-dlp for flat playlist metadata without downloading media."""
    ytdlp_cmd = get_ytdlp_cmd()

    # Normalize YouTube channel streams URL
    url = channel_url.strip()
    if "youtube.com" in url and not url.endswith(("/streams", "/videos")):
        url = url.rstrip("/") + "/streams"

    cmd = [
        *ytdlp_cmd,
        "--flat-playlist",
        "--dump-single-json",
        "--playlist-end",
        str(max_items),
        "--skip-download",
        "--no-warnings",
        url,
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        if proc.returncode != 0:
            # Fallback without /streams suffix if failed
            if url.endswith("/streams"):
                alt_url = url[:-8] + "/videos"
                cmd[cmd.index(url)] = alt_url
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
            if proc.returncode != 0:
                return []

        data = json.loads(proc.stdout)
        entries = data.get("entries") or []
        results = []
        for e in entries:
            if not e:
                continue
            v_id = e.get("id")
            v_title = e.get("title") or "Untitled Stream"
            v_url = e.get("url") or f"https://www.youtube.com/watch?v={v_id}"
            duration = e.get("duration") or 0
            views = e.get("view_count") or 0
            uploader = e.get("uploader") or data.get("channel") or data.get("uploader") or "Streamer"
            upload_date = e.get("upload_date") or ""

            results.append({
                "id": v_id,
                "title": v_title,
                "url": v_url,
                "duration": duration,
                "views": views,
                "uploader": uploader,
                "upload_date": upload_date,
                "channel_url": channel_url,
            })
        return results
    except Exception as e:
        print(f"[VOD Watcher] Notice: Could not fetch {channel_url}: {e}")
        return []


def score_vod_candidate(vod: dict, viral_weights: dict) -> tuple[float, dict]:
    """Calculates a recommendation score (0-100) based on view velocity, recency, and streamer weights."""
    streamer_weights = viral_weights.get("streamer_source_weights", {})
    uploader = vod.get("uploader", "")
    s_name = uploader.split("(")[0].strip()

    # 1. Base Streamer Weight (Max 40 pts)
    s_dat = streamer_weights.get(s_name, {})
    s_wt = float(s_dat.get("weight", 1.0))
    streamer_pts = round(min(40.0, max(5.0, s_wt * 22.0)), 1)

    # 2. View Count / Velocity (Max 35 pts)
    views = vod.get("views") or 0
    if views > 100000:
        view_pts = 35.0
    elif views > 50000:
        view_pts = 30.0
    elif views > 20000:
        view_pts = 24.0
    elif views > 5000:
        view_pts = 18.0
    else:
        view_pts = 10.0

    # 3. Recency Bonus (Max 25 pts)
    upload_date = vod.get("upload_date") or ""
    recency_pts = 20.0  # Default recent
    if upload_date and len(upload_date) == 8:
        try:
            d = datetime.datetime.strptime(upload_date, "%Y%m%d").date()
            diff_days = (datetime.date.today() - d).days
            if diff_days <= 1:
                recency_pts = 25.0
            elif diff_days <= 3:
                recency_pts = 20.0
            elif diff_days <= 7:
                recency_pts = 14.0
            else:
                recency_pts = 5.0
        except Exception:
            pass

    total_score = round(min(100.0, max(10.0, streamer_pts + view_pts + recency_pts)), 1)
    breakdown = {
        "streamer_pts": streamer_pts,
        "streamer_weight": s_wt,
        "view_pts": view_pts,
        "recency_pts": recency_pts,
        "total": total_score,
    }
    return total_score, breakdown


def check_new_streams(verbose: bool = True) -> list[dict]:
    """Checks all watched streamer channels and returns unclipped fresh streams sorted by score."""
    cfg = load_watched_streamers_config()
    streamers = cfg.get("streamers", [])
    scan_settings = cfg.get("scan_settings", {})
    max_per_channel = scan_settings.get("max_streams_per_channel", 3)

    if not streamers:
        if verbose:
            print("[VOD Watcher] No streamer channels configured in config/watched_streamers.json.")
            print("Add channels via 'python scripts/vod_watcher.py --add <URL> <NAME>'")
        return []

    processed_ids = get_already_processed_ids()
    viral_weights = load_viral_dna_weights()

    if verbose:
        print("=" * 75)
        print("📺 AUTO-VOD STREAMER WATCHER — SCANNING APPROVED CHANNELS")
        print(f"Channels configured: {len(streamers)}")
        print("=" * 75)

    fresh_streams = []

    for s in streamers:
        c_name = s.get("name", "Creator")
        c_url = s.get("url")
        if not c_url:
            continue

        if verbose:
            print(f"  Scanning: {c_name} ({c_url})...")

        items = fetch_channel_recent_streams(c_url, max_items=max_per_channel)
        for item in items:
            v_id = item.get("id")
            v_url = item.get("url")

            # Check if already processed
            if v_id in processed_ids or v_url in processed_ids:
                continue

            score, breakdown = score_vod_candidate(item, viral_weights)
            item["score"] = score
            item["score_breakdown"] = breakdown
            fresh_streams.append(item)

    # Sort highest score first
    fresh_streams.sort(key=lambda x: x.get("score", 0), reverse=True)

    if verbose:
        print("\n" + "=" * 75)
        print("🎯 FRESH UNCLIPPED STREAMS AVAILABLE FOR PROCESSING")
        print("=" * 75)

        if not fresh_streams:
            print("All streams across watched channels have already been logged or queued.")
            print("No new unclipped streams found.")
        else:
            print(f"Found {len(fresh_streams)} fresh candidate stream(s):\n")
            for idx, stream in enumerate(fresh_streams, 1):
                uploader = stream.get("uploader")
                title = stream.get("title")
                dur_m = int((stream.get("duration") or 0) / 60)
                views = stream.get("views") or 0
                sc = stream.get("score", 0)
                wt = stream.get("score_breakdown", {}).get("streamer_weight", 1.0)
                url = stream.get("url")

                dur_str = f"{dur_m // 60}h {dur_m % 60}m" if dur_m >= 60 else f"{dur_m} mins"
                print(f"[#{idx}] {uploader} — \"{title}\"")
                print(f"     • Stats:          {views:,} views | Duration: {dur_str}")
                print(f"     • Viral Score:    {sc} / 100 (Streamer weight: {wt}x)")
                print(f"     • Stream URL:     {url}")
                print(f"     👉 To clip this stream: reply \"clip #{idx}\" or run:")
                print(f"        python main.py \"{url}\"")
                print()

        print("-" * 75)
        print("Tip: Run 'python main.py <URL>' to begin atomic 1-clip-at-a-time processing.")
        print("=" * 75)

    return fresh_streams


def add_streamer_channel(url: str, name: str, niche: str = "GTA 6 / Gaming", priority: float = 1.0):
    cfg = load_watched_streamers_config()
    streamers = cfg.get("streamers", [])

    # Check if already present
    for s in streamers:
        if s.get("url") == url:
            print(f"[VOD Watcher] Streamer channel already watched: {s.get('name')}")
            return

    streamers.append({
        "name": name,
        "platform": "youtube",
        "url": url,
        "niche": niche,
        "priority_weight": priority,
        "notes": "Added via CLI / chat command",
    })
    cfg["streamers"] = streamers
    save_watched_streamers_config(cfg)
    print(f"✅ Added '{name}' ({url}) to watched streamer channels in config/watched_streamers.json.")


def list_watched_streamers():
    cfg = load_watched_streamers_config()
    streamers = cfg.get("streamers", [])
    print("=" * 75)
    print("📋 WATCHED STREAMER CHANNELS (config/watched_streamers.json)")
    print("=" * 75)
    if not streamers:
        print("No channels watched yet. Add one with --add <URL> <NAME>.")
    else:
        for idx, s in enumerate(streamers, 1):
            print(f"[#{idx}] {s.get('name')} ({s.get('niche')})")
            print(f"     • URL:      {s.get('url')}")
            print(f"     • Priority: {s.get('priority_weight', 1.0)}x")
            print(f"     • Notes:    {s.get('notes', '')}")
            print()
    print("=" * 75)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-VOD Streamer Watcher")
    parser.add_argument("--check", action="store_true", help="Check watched channels for fresh unclipped streams")
    parser.add_argument("--add", nargs=2, metavar=("URL", "NAME"), help="Add a new streamer channel to watch")
    parser.add_argument("--list", action="store_true", help="List watched streamer channels")
    parser.add_argument("--json", action="store_true", help="Output fresh streams as JSON")
    args = parser.parse_args()

    if args.add:
        add_streamer_channel(url=args.add[0], name=args.add[1])
    elif args.list:
        list_watched_streamers()
    else:
        streams = check_new_streams(verbose=not args.json)
        if args.json:
            print(json.dumps(streams, indent=2))
