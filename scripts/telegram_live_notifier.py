"""Smart, Zero-Cost Both-Live Telegram Notifier for GTA 6 Clipper Automation.

Delivers ONE clean Telegram notification immediately once BOTH the YouTube Short
and Instagram Reel are publicly live, with a 5-minute failsafe.
"""

import argparse
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Ensure immediate unbuffered console logging
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import BASE_DIR, ENV_PATH, PUBLISHED_JSON, load_env
from zernio_client import ZernioClient

IST_OFFSET = datetime.timedelta(hours=5, minutes=30)


def get_telegram_config() -> tuple[str, str]:
    env_vars = load_env()
    token = env_vars.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = env_vars.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
    return token, chat_id


def send_telegram_message(text: str) -> bool:
    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        print("[Telegram] Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "GTA6-Telegram-Notifier/2.0"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("ok", False)
    except Exception as e:
        print(f"[Telegram] Error sending message: {e}")
        return False


def check_youtube_public(yt_url: str) -> bool:
    """Zero-cost, lightweight public check via YouTube's official oEmbed endpoint.

    Returns True ONLY if video is public and accessible.
    """
    if not yt_url:
        return False
    oembed_url = f"https://www.youtube.com/oembed?url={urllib.parse.quote(yt_url)}&format=json"
    req = urllib.request.Request(
        oembed_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return bool(data.get("title"))
    except Exception:
        return False
    return False


def format_ist(dt: datetime.datetime) -> str:
    ist_time = dt.astimezone(datetime.timezone(IST_OFFSET))
    return ist_time.strftime("%I:%M:%S %p")


def format_ist_deadline(dt: datetime.datetime, minutes: int = 30) -> str:
    deadline = dt.astimezone(datetime.timezone(IST_OFFSET)) + datetime.timedelta(minutes=minutes)
    return deadline.strftime("%I:%M:%S %p")


def update_published_clip_log(post_id: str, yt_url: str, ig_url: str, notified: bool = True):
    if not PUBLISHED_JSON.exists():
        return
    try:
        with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
            pubs = json.load(f)
        modified = False
        for p in pubs:
            if p.get("post_id") == post_id:
                if yt_url:
                    p["youtube_url"] = yt_url
                if ig_url:
                    p["instagram_url"] = ig_url
                p["status"] = "published"
                if notified:
                    p["telegram_notified"] = True
                p["notified_at"] = datetime.datetime.now().astimezone().isoformat()
                modified = True
                break
        if modified:
            with open(PUBLISHED_JSON, "w", encoding="utf-8") as f:
                json.dump(pubs, f, indent=2)
            print(f"[Notifier] Updated logs/published_clips.json for post {post_id}")
    except Exception as e:
        print(f"[Notifier] Error updating published_clips.json: {e}")


def watch_clip_publication(client: ZernioClient, clip_entry: dict, max_poll_minutes: int = 12) -> bool:
    post_id = clip_entry.get("post_id")
    clip_id = clip_entry.get("clip_id")
    campaign = clip_entry.get("campaign_name", load_active_campaign().get("campaign_name", "GTA VI Clipping Campaign"))
    sched_utc = clip_entry.get("scheduled_for")

    print(f"\n[Notifier] Monitoring Clip #{clip_id} (Post ID: {post_id}, Scheduled: {sched_utc})...")

    start_poll_time = time.time()
    max_seconds = max_poll_minutes * 60
    poll_interval = 25  # seconds (2.4 req/min, well under 60 req/min limit)

    first_live_time = None
    first_live_plat = None
    first_live_url = None
    failsafe_5min_alert_sent = False

    while (time.time() - start_poll_time) < max_seconds:
        try:
            res = client.get_post(post_id)
            post = res.get("post", {})
            platforms = post.get("platforms", [])

            yt_plat = next((p for p in platforms if p.get("platform") == "youtube"), {})
            ig_plat = next((p for p in platforms if p.get("platform") == "instagram"), {})

            yt_status = yt_plat.get("status", "pending")
            ig_status = ig_plat.get("status", "pending")
            yt_url = yt_plat.get("platformPostUrl") or (f"https://www.youtube.com/watch?v={yt_plat.get('platformPostId')}" if yt_plat.get("platformPostId") else "")
            ig_url = ig_plat.get("platformPostUrl") or ""

            # Check for failure on either platform
            if yt_status == "failed" or ig_status == "failed":
                failed_name = "YouTube" if yt_status == "failed" else "Instagram"
                err_msg = yt_plat.get("lastError") or ig_plat.get("lastError") or "Unknown platform publish error"
                alert_text = (
                    f"🚨 *CLIP #{clip_id} PUBLISH FAILURE ALERT*\n"
                    f"🎮 *Campaign:* {campaign}\n"
                    f"❌ *Failed Platform:* `{failed_name}`\n"
                    f"⚠️ *Error:* `{err_msg}`\n"
                    f"🔍 *Post ID:* `{post_id}`"
                )
                print(f"[Notifier] FAILURE on {failed_name}: {err_msg}")
                send_telegram_message(alert_text)
                return False

            yt_is_live = (yt_status == "published") and bool(yt_url)
            ig_is_live = (ig_status == "published") and bool(ig_url)

            # Validate YouTube is public
            if yt_is_live:
                yt_is_public = check_youtube_public(yt_url)
                if not yt_is_public:
                    print(f"[Notifier] YouTube post URL returned but video not yet public on oEmbed ({yt_url}). Waiting...")
                    yt_is_live = False

            # Check if BOTH are live
            if yt_is_live and ig_is_live:
                now_dt = datetime.datetime.now(datetime.timezone.utc)
                now_ist = format_ist(now_dt)
                deadline_ist = format_ist_deadline(now_dt, 30)

                message = (
                    f"🚀 *CLIP #{clip_id} IS LIVE ON BOTH PLATFORMS!*\n"
                    f"🎮 *Campaign:* {campaign}\n"
                    f"⏰ *Live Time:* `{now_ist} IST`\n"
                    f"⚠️ *Whop 30-Min Deadline:* `{deadline_ist} IST`\n\n"
                    f"🔴 *YouTube Short (Live & Public):*\n`{yt_url}`\n\n"
                    f"🟣 *Instagram Reel (Live):*\n`{ig_url}`\n\n"
                    f"📋 _Both links verified! Submit on Whop now._"
                )
                print(f"[Notifier] Clip #{clip_id} is live on BOTH platforms! Sending Telegram notification...")
                success = send_telegram_message(message)
                if success:
                    print("[Notifier] Telegram message delivered successfully!")
                    update_published_clip_log(post_id, yt_url, ig_url, notified=True)
                    return True
                else:
                    print("[Notifier] Warning: send_telegram_message returned False.")
                    return False

            # Check 5-minute failsafe if ONE platform is live but the second isn't
            if (yt_is_live and not ig_is_live) or (ig_is_live and not yt_is_live):
                current_time = time.time()
                if first_live_time is None:
                    first_live_time = current_time
                    first_live_plat = "YouTube Short" if yt_is_live else "Instagram Reel"
                    first_live_url = yt_url if yt_is_live else ig_url
                    print(f"[Notifier] First platform live: {first_live_plat} at {first_live_url}. Waiting for second platform...")
                elif (current_time - first_live_time) >= 300 and not failsafe_5min_alert_sent:
                    # 5 minutes have elapsed since the first platform went live
                    now_dt = datetime.datetime.now(datetime.timezone.utc)
                    pending_plat = "Instagram Reel" if yt_is_live else "YouTube Short"
                    pending_status = ig_status if yt_is_live else yt_status

                    failsafe_msg = (
                        f"⚠️ *CLIP #{clip_id} PARTIAL LIVE ALERT (5-Min Failsafe)*\n"
                        f"🎮 *Campaign:* {campaign}\n"
                        f"⏰ *Current Time:* `{format_ist(now_dt)} IST`\n\n"
                        f"✅ *Live Platform ({first_live_plat}):*\n`{first_live_url}`\n\n"
                        f"⏳ *Pending Platform ({pending_plat}):* Status is `{pending_status}`.\n"
                        f"_Will send the second link the second it goes live!_"
                    )
                    print(f"[Notifier] 5-minute failsafe triggered! Sending partial alert...")
                    send_telegram_message(failsafe_msg)
                    failsafe_5min_alert_sent = True

            print(f"[Notifier] Clip #{clip_id} status: YT={yt_status} ({'LIVE' if yt_is_live else 'waiting'}), IG={ig_status} ({'LIVE' if ig_is_live else 'waiting'}). Polling again in {poll_interval}s...")

        except Exception as e:
            print(f"[Notifier] Error polling post {post_id}: {e}")

        time.sleep(poll_interval)

    print(f"[Notifier] Max polling time ({max_poll_minutes}m) exceeded for Clip #{clip_id}.")
    return False


def run_watcher(single_pass: bool = False):
    print("=" * 60)
    print("🤖 GTA 6 BOTH-LIVE TELEGRAM NOTIFIER")
    print("=" * 60)

    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        print("[Notifier] FATAL: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")
        sys.exit(1)

    print(f"[Notifier] Telegram Bot configured | Target Chat ID: {chat_id}")
    client = ZernioClient()

    while True:
        if not PUBLISHED_JSON.exists():
            print("[Notifier] logs/published_clips.json not found. Waiting...")
            if single_pass:
                break
            time.sleep(30)
            continue

        with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
            pubs = json.load(f)

        clipup_clips = [p for p in pubs if p.get("campaign_name") == load_active_campaign().get("campaign_name", "GTA VI Clipping Campaign")]
        unnotified = [p for p in clipup_clips if not p.get("telegram_notified")]

        if not unnotified:
            print("[Notifier] No pending unnotified clips found.")
            if single_pass:
                break
            time.sleep(30)
            continue

        print(f"[Notifier] Found {len(unnotified)} unnotified clip(s). Checking scheduled times...")
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        for clip in unnotified:
            sched_str = clip.get("scheduled_for")
            if not sched_str:
                continue

            try:
                # Handle formats with or without .000Z
                clean_sched = sched_str.replace("Z", "+00:00")
                sched_dt = datetime.datetime.fromisoformat(clean_sched)
            except Exception:
                sched_dt = now_utc

            diff_seconds = (now_utc - sched_dt).total_seconds()

            # If clip is scheduled within 3 minutes in the future, or in the past (up to 4 hours ago), monitor it
            if diff_seconds >= -180 and diff_seconds <= 14400:
                print(f"[Notifier] Clip #{clip.get('clip_id')} is active (Scheduled: {sched_str}, diff: {int(diff_seconds)}s). Starting watcher...")
                watch_clip_publication(client, clip)
            else:
                print(f"[Notifier] Clip #{clip.get('clip_id')} scheduled at {sched_str} (in {int(-diff_seconds/60)} min). Standing by.")

        if single_pass:
            break

        print("[Notifier] Sleeping 30s before next queue check...")
        time.sleep(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Both-Live Telegram Notifier")
    parser.add_argument("--once", action="store_true", help="Run single pass and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in background")
    args = parser.parse_args()

    run_watcher(single_pass=args.once and not args.daemon)
