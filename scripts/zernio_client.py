"""Zernio API v1 Client.

Handles multi-platform scheduling for Instagram Reels and YouTube Shorts
using Zernio free tier / API v1 endpoints with scheduledFor.
"""

import datetime
import json
import os
import sys
import time
from pathlib import Path
import requests

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    ACCOUNTS_PATH,
    get_zernio_api_key,
    load_zernio_accounts,
    save_zernio_accounts,
)

BASE_URL = "https://api.zernio.com/v1"


class ZernioClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or get_zernio_api_key()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def discover_and_save_accounts(self) -> dict:
        url = f"{BASE_URL}/accounts"
        resp = self.session.get(url, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch accounts from Zernio: {resp.status_code} {resp.text}")

        data = resp.json()
        accounts = data.get("accounts") or data if isinstance(data, list) else []

        ig_acc = None
        yt_acc = None

        for acc in accounts:
            p = (acc.get("platform") or "").lower()
            if p == "instagram" and not ig_acc:
                ig_acc = acc
            elif p in ("youtube", "youtube_shorts") and not yt_acc:
                yt_acc = acc

        result = {
            "instagram": {
                "account_id": ig_acc.get("_id") or ig_acc.get("id") if ig_acc else None,
                "name": ig_acc.get("name") if ig_acc else None,
                "platform": "instagram",
            },
            "youtube": {
                "account_id": yt_acc.get("_id") or yt_acc.get("id") if yt_acc else None,
                "name": yt_acc.get("name") if yt_acc else None,
                "platform": "youtube",
            },
            "discovered_at": datetime.datetime.now().astimezone().isoformat(),
        }

        save_zernio_accounts(result)
        return result

    def upload_media(self, file_path: Path) -> str:
        url = f"{BASE_URL}/media/upload"
        filename = file_path.name
        headers = {"Authorization": f"Bearer {self.api_key}"}

        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "video/mp4")}
            resp = requests.post(url, headers=headers, files=files, timeout=300)

        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Media upload failed: {resp.status_code} {resp.text}")

        data = resp.json()
        media_url = data.get("url") or data.get("mediaUrl") or data.get("fileUrl")
        if not media_url:
            raise ValueError(f"No media URL in upload response: {data}")
        return media_url

    def schedule_clip(
        self,
        clip_path: Path,
        title: str,
        caption: str,
        first_comment: str = None,
        thumb_path: Path = None,
        campaign: dict = None,
        scheduled_for: str = None,
        queue_index: int = 0,
    ) -> dict:
        accs = load_zernio_accounts()
        ig_id = accs.get("instagram", {}).get("account_id")
        yt_id = accs.get("youtube", {}).get("account_id")

        account_ids = [aid for aid in [ig_id, yt_id] if aid and not aid.startswith("acc_")]
        if not account_ids:
            return {
                "status": "dry_run",
                "post_id": f"mock_post_{int(time.time())}",
                "scheduled_for": scheduled_for or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "details": "No real account IDs connected; dry run completed.",
            }

        media_url = self.upload_media(clip_path)

        payload = {
            "accountIds": account_ids,
            "mediaUrls": [media_url],
            "title": title,
            "content": caption,
            "scheduledFor": scheduled_for,
            "platforms": {
                "instagram": {
                    "contentType": "reel",
                    "firstComment": first_comment,
                },
                "youtube": {
                    "contentType": "short",
                    "title": title,
                    "visibility": "public",
                },
            },
        }

        url = f"{BASE_URL}/posts"
        resp = self.session.post(url, json=payload, timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Zernio post creation failed: {resp.status_code} {resp.text}")

        res_data = resp.json()
        post_id = res_data.get("id") or res_data.get("_id") or res_data.get("postId")
        return {
            "status": "scheduled",
            "post_id": post_id,
            "scheduled_for": scheduled_for,
            "media_url": media_url,
        }

    def get_post_status(self, post_id: str) -> dict:
        url = f"{BASE_URL}/posts/{post_id}"
        resp = self.session.get(url, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch post status: {resp.status_code} {resp.text}")
        return resp.json()
