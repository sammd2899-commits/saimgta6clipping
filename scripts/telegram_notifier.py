"""Instant Telegram Notifier for GTA 6 Clipper Automation.

Delivers newly live YouTube Short & Instagram Reel URLs straight to mobile
with 0-second latency for immediate Whop Content Rewards submission.
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import BASE_DIR, ENV_PATH, PUBLISHED_JSON
from zernio_client import ZernioClient


def get_telegram_config() -> tuple[str, str]:
    token = None
    chat_id = None

    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                elif line.startswith("TELEGRAM_CHAT_ID="):
                    chat_id = line.split("=", 1)[1].strip()

    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    return token, chat_id


def save_chat_id(chat_id: str):
    token, _ = get_telegram_config()
    lines = []
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if not line.startswith("TELEGRAM_CHAT_ID="):
                    lines.append(line.rstrip("\r\n"))
    lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[Telegram] Saved Chat ID: {chat_id} to .env")


def auto_detect_chat_id(max_wait_seconds: int = 60) -> str:
    token, chat_id = get_telegram_config()
    if chat_id:
        return chat_id

    if not token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env")

    print("[Telegram] Listening for your start message on your bot...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    req = urllib.request.Request(url, headers={"User-Agent": "GTA6-Clipper-Bot/1.0"})

    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = data.get("result", [])
                for update in results:
                    msg = update.get("message", {})
                    chat = msg.get("chat", {})
                    cid = chat.get("id")
                    if cid:
                        save_chat_id(str(cid))
                        return str(cid)
        except Exception as e:
            print(f"[Telegram] Error checking getUpdates: {e}")
        time.sleep(2)

    return None


def send_telegram_message(text: str) -> bool:
    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        print("[Telegram] Bot token or chat_id not configured yet.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "GTA6-Clipper-Bot/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("ok", False)
    except Exception as e:
        print(f"[Telegram] Failed to send message: {e}")
        return False


def notify_live_clips():
    """Checks for newly live clips and sends instant push notification."""
    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        return

    if not PUBLISHED_JSON.exists():
        return

    with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
        clips = json.load(f)

    client = ZernioClient()
    updated = False

    for c in clips:
        pid = c.get("post_id")
        if not pid:
            continue

        # If already notified via telegram, skip
        if c.get("telegram_notified"):
            continue

        try:
            p_resp = client.get_post(pid)
            post = p_resp.get("post", {})
            platforms = post.get("platforms", [])

            yt_url = next((pl.get("platformPostUrl") for pl in platforms if pl.get("platform") == "youtube" and pl.get("status") == "published"), None)
            ig_url = next((pl.get("platformPostUrl") for pl in platforms if pl.get("platform") == "instagram" and pl.get("status") == "published"), None)

            # Check if at least one URL is live
            if yt_url or ig_url:
                c["youtube_url"] = yt_url or c.get("youtube_url")
                c["instagram_url"] = ig_url or c.get("instagram_url")

                slot = c.get("scheduled_ist") or "Live Now"
                title = c.get("title", f"Clip #{c.get('clip_id')}")

                msg = (
                    f"🚀 *GTA 6 CLIP IS LIVE!* ({slot})\n\n"
                    f"🎬 *{title}*\n\n"
                    f"📺 *YouTube Short (Tap to copy):*\n"
                    f"`{c.get('youtube_url', 'Processing...')}`\n\n"
                    f"📸 *Instagram Reel (Tap to copy):*\n"
                    f"`{c.get('instagram_url', 'Processing...')}`\n\n"
                    f"👉 Copy the link above and paste into Whop right away!"
                )

                if send_telegram_message(msg):
                    print(f"[Telegram] Sent instant alert for Clip #{c.get('clip_id')}")
                    c["telegram_notified"] = True
                    updated = True

        except Exception as e:
            print(f"[Telegram] Error checking post {pid}: {e}")

    if updated:
        with open(PUBLISHED_JSON, "w", encoding="utf-8") as f:
            json.dump(clips, f, indent=2)


def watch_schedule(interval_seconds: int = 30):
    """Monitors scheduled posts and instantly pings Telegram when they go live."""
    print(f"[Telegram Watcher] Started monitoring. Checking every {interval_seconds}s...")
    while True:
        try:
            notify_live_clips()
        except Exception as e:
            print(f"[Telegram Watcher] Check error: {e}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    if "--detect" in sys.argv:
        cid = auto_detect_chat_id()
        if cid:
            print(f"Connected! Chat ID: {cid}")
            send_telegram_message("🎉 *GTA 6 Clipper Bot Connected!*\nYou will now receive instant links for every published clip directly on your phone.")
        else:
            print("Timed out. Make sure you tapped Start on your bot.")
    elif "--test" in sys.argv:
        send_telegram_message("🔔 *Test notification from GTA 6 Clipper!*\nInstant mobile delivery is working.")
    elif "--watch" in sys.argv:
        watch_schedule()
    else:
        notify_live_clips()
