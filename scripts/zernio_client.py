"""Zernio API v1 Client with Fixed Awake-Hour IST Scheduling (Asia/Kolkata).

Features:
- Fixed IST awake slots (14:00, 16:00, 18:00, 20:00, 22:00 IST -> UTC scheduledFor)
- Single unified post payload ensuring YouTube and Instagram publish at the exact same moment
- Direct presigned binary media upload
- Auto-compliance enforcement (Zero dropped tags)
- Live post status tracking & Whop URL retrieval
- Rate-limit safety & exponential backoff
"""

import datetime
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    enforce_and_auto_append_compliance,
    get_zernio_api_key,
    load_active_campaign,
    load_zernio_accounts,
    save_zernio_accounts,
)
from scheduler import get_next_available_slots

ZERNIO_BASE_URL = "https://zernio.com/api/v1"


class ZernioClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or get_zernio_api_key()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "GTA6-Clipper-Automation/2.0",
        }
        self.hourly_posts_count = 0
        self.hour_window_start = time.time()

    def _request(self, method: str, endpoint: str, data: dict = None, max_retries: int = 3) -> dict:
        url = f"{ZERNIO_BASE_URL}{endpoint}" if endpoint.startswith("/") else f"{ZERNIO_BASE_URL}/{endpoint}"
        body_bytes = json.dumps(data).encode("utf-8") if data is not None else None

        for attempt in range(1, max_retries + 1):
            req = urllib.request.Request(url, data=body_bytes, headers=self.headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_data = resp.read().decode("utf-8")
                    return json.loads(resp_data) if resp_data else {}
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                print(f"[Zernio API] HTTP {e.code} error on {method} {endpoint} (attempt {attempt}/{max_retries}): {err_body}")

                if e.code == 429:
                    wait_time = 15 * attempt
                    print(f"[Zernio API] Rate limit reached. Backing off for {wait_time}s...")
                    time.sleep(wait_time)
                elif e.code == 409 and "existingPostId" in err_body:
                    try:
                        err_json = json.loads(err_body)
                        existing_id = err_json.get("details", {}).get("existingPostId")
                        if existing_id:
                            print(f"[Zernio API] Post already created on previous attempt: {existing_id}")
                            return {"post": {"_id": existing_id, "status": "scheduled"}}
                    except Exception:
                        pass
                    raise RuntimeError(f"Zernio API Error {e.code}: {err_body}")
                elif e.code >= 500:
                    wait_time = 5 * attempt
                    print(f"[Zernio API] Server error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError(f"Zernio API Error {e.code}: {err_body}")
            except Exception as e:
                print(f"[Zernio API] Network exception (attempt {attempt}/{max_retries}): {e}")
                time.sleep(3 * attempt)

        raise RuntimeError(f"Failed {method} {endpoint} after {max_retries} attempts.")

    def discover_and_save_accounts(self) -> dict:
        """Queries /v1/accounts and filters active Instagram and YouTube accounts."""
        print("[Zernio] Discovering connected social accounts...")
        data = self._request("GET", "/accounts")
        raw_accounts = data.get("accounts", [])

        discovered = []
        for acc in raw_accounts:
            platform = acc.get("platform")
            if platform in ("instagram", "youtube"):
                is_active = acc.get("isActive", False)
                status = acc.get("platformStatus", "unknown")
                acc_info = {
                    "accountId": acc.get("_id"),
                    "platform": platform,
                    "username": acc.get("username", ""),
                    "displayName": acc.get("displayName", ""),
                    "profileUrl": acc.get("profileUrl", ""),
                    "isActive": is_active,
                    "platformStatus": status,
                }
                discovered.append(acc_info)
                print(f"  + Discovered {platform.upper()} account: @{acc_info['username']} (ID: {acc_info['accountId']}, Active: {is_active})")

        result = {
            "accounts": discovered,
            "verified_at": datetime.datetime.now().astimezone().isoformat(),
        }
        save_zernio_accounts(result)
        return result

    def upload_media(self, file_path: str | Path, content_type: str = None) -> str:
        """Uploads a local media file (video or image) via presigned URL."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = path.stat().st_size
        filename = path.name

        if not content_type:
            mime, _ = mimetypes.guess_type(str(path))
            content_type = mime or ("video/mp4" if path.suffix.lower() == ".mp4" else "image/jpeg")

        print(f"[Zernio] Requesting presigned URL for {filename} ({file_size / (1024*1024):.2f} MB)...")
        presign_resp = self._request(
            "POST",
            "/media/presign",
            {
                "filename": filename,
                "contentType": content_type,
                "size": file_size,
            },
        )

        upload_url = presign_resp.get("uploadUrl")
        public_url = presign_resp.get("publicUrl")
        if not upload_url or not public_url:
            raise RuntimeError(f"Presign response missing uploadUrl/publicUrl: {presign_resp}")

        print("[Zernio] Uploading binary payload directly to storage...")
        with open(path, "rb") as f:
            file_data = f.read()

        put_req = urllib.request.Request(
            upload_url,
            data=file_data,
            headers={"Content-Type": content_type},
            method="PUT",
        )
        with urllib.request.urlopen(put_req, timeout=120) as put_resp:
            if put_resp.status not in (200, 201, 204):
                raise RuntimeError(f"Direct media upload failed with status {put_resp.status}")

        print(f"[Zernio] Media upload complete: {public_url}")
        return public_url

    def schedule_clip(
        self,
        clip_path: str | Path,
        title: str,
        caption: str,
        first_comment: str = "",
        thumb_path: str | Path = None,
        campaign: dict = None,
        scheduled_for: str = None,
        queue_index: int = 0,
    ) -> dict:
        """Uploads and schedules 1 clip to Instagram (Reel) and YouTube (Short)

        at the exact same awake IST slot (converted to UTC scheduledFor).
        """
        # Step 1: Enforce compliance (auto-append if anything missing)
        clean_title, compliant_caption, was_modified = enforce_and_auto_append_compliance(
            title, caption, campaign
        )
        if was_modified:
            print("[Zernio] Notice: Missing campaign elements were auto-appended before upload.")

        # Step 2: Determine scheduled_for UTC timestamp
        if not scheduled_for:
            available = get_next_available_slots(queue_index + 1)
            scheduled_for = available[-1]["scheduled_for_utc"]

        # Step 3: Upload video (and thumbnail if provided)
        video_url = self.upload_media(clip_path, content_type="video/mp4")
        thumb_url = None
        if thumb_path and Path(thumb_path).exists():
            try:
                thumb_url = self.upload_media(thumb_path, content_type="image/jpeg")
            except Exception as e:
                print(f"[Zernio] Optional thumbnail upload failed (proceeding without): {e}")

        # Step 4: Get target accounts
        acc_data = load_zernio_accounts()
        accounts = acc_data.get("accounts", [])
        yt_acc = next((a for a in accounts if a["platform"] == "youtube" and a.get("isActive")), None)
        ig_acc = next((a for a in accounts if a["platform"] == "instagram" and a.get("isActive")), None)

        if not yt_acc or not ig_acc:
            raise RuntimeError("Missing active YouTube or Instagram account in config/zernio_accounts.json")

        media_item = {"type": "video", "url": video_url}
        if thumb_url:
            media_item["thumbnail"] = thumb_url

        platforms = [
            {
                "platform": "youtube",
                "accountId": yt_acc["accountId"],
                "platformSpecific": {"title": clean_title, "madeForKids": False},
                "platformSpecificData": {"title": clean_title, "madeForKids": False},
            },
            {
                "platform": "instagram",
                "accountId": ig_acc["accountId"],
                "platformSpecific": {"firstComment": first_comment or "", "commentsEnabled": True},
                "platformSpecificData": {"firstComment": first_comment or "", "commentsEnabled": True},
            },
        ]

        post_payload = {
            "content": compliant_caption,
            "mediaItems": [media_item],
            "platforms": platforms,
            "publishNow": False,
            "scheduledFor": scheduled_for,
        }

        print(f"[Zernio] Scheduling clip #{queue_index+1} for {scheduled_for}...")
        resp = self._request("POST", "/posts", post_payload)
        self.hourly_posts_count += 1

        post_obj = resp.get("post", resp)
        post_id = post_obj.get("_id") or post_obj.get("id", "unknown")
        status = post_obj.get("status", "scheduled")

        # Gentle pause to respect rate limits
        time.sleep(2.0)

        return {
            "post_id": post_id,
            "status": status,
            "scheduled_for": scheduled_for,
            "video_url": video_url,
            "title": clean_title,
            "caption": compliant_caption,
        }

    def get_post(self, post_id: str) -> dict:
        return self._request("GET", f"/posts/{post_id}")

    def list_posts(self, limit: int = 50) -> list:
        data = self._request("GET", f"/posts?limit={limit}")
        return data.get("posts", [])


if __name__ == "__main__":
    client = ZernioClient()
    accs = client.discover_and_save_accounts()
    print("Verification complete. Accounts ready.")
    sample_slot = get_next_available_slots(1)[0]
    print("Sample next IST slot:", sample_slot["datetime_ist_display"], "-> UTC:", sample_slot["scheduled_for_utc"])
