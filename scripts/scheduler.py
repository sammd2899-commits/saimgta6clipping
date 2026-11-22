"""Fixed Awake-Hour IST Scheduler Engine (Asia/Kolkata).

Manages 5 clips/day warm-up slots: 14:00, 16:00, 18:00, 20:00, 22:00 IST.
Accurately maps IST awake slots to ISO 8601 UTC for Zernio scheduledFor,
prevents slot collisions, rolls cleanly across days, and guarantees zero overnight posts.
"""

import datetime
import json
import os
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import BASE_DIR, CONFIG_DIR, PUBLISHED_JSON, QUEUE_PATH

SCHEDULE_CONFIG_PATH = CONFIG_DIR / "schedule_config.json"
IST_TZ = datetime.timezone(datetime.timedelta(hours=5, minutes=30), name="IST")


def load_schedule_config() -> dict:
    if not SCHEDULE_CONFIG_PATH.exists():
        default_cfg = {
            "timezone": "Asia/Kolkata",
            "utc_offset_hours": 5.5,
            "daily_slots_ist": ["14:00", "16:00", "18:00", "20:00", "22:00"],
            "max_clips_per_day": 5,
            "min_lead_minutes": 15,
            "notes": "5-day warm-up schedule for new accounts; I will update this later to 8/day.",
            "updated_at": datetime.datetime.now().astimezone().isoformat(),
        }
        save_schedule_config(default_cfg)
        return default_cfg

    with open(SCHEDULE_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schedule_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg["updated_at"] = datetime.datetime.now().astimezone().isoformat()
    with open(SCHEDULE_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_already_reserved_utc_slots() -> set[str]:
    """Scans published_clips.json and job_queue.json to identify already booked UTC slots."""
    reserved = set()

    # Check published_clips.json
    if PUBLISHED_JSON.exists():
        try:
            with open(PUBLISHED_JSON, "r", encoding="utf-8") as f:
                records = json.load(f)
                for r in records:
                    s = r.get("scheduled_for")
                    if s:
                        reserved.add(s)
        except Exception:
            pass

    # Check job_queue.json
    if QUEUE_PATH.exists():
        try:
            with open(QUEUE_PATH, "r", encoding="utf-8") as f:
                q = json.load(f)
                for c in q.get("clips", []):
                    s = c.get("scheduled_for")
                    if s and c.get("status") in ("SCHEDULED", "PENDING"):
                        reserved.add(s)
        except Exception:
            pass

    return reserved


def get_next_available_slots(count: int, from_dt_ist: datetime.datetime = None) -> list[dict]:
    """Assigns the next 'count' available future slots from daily_slots_ist.

    Rolls cleanly across days once a day's slots are full.
    Converts IST to ISO 8601 UTC with absolute precision (14:00 IST -> 08:30:00Z).
    """
    cfg = load_schedule_config()
    daily_slots = cfg.get("daily_slots_ist", ["14:00", "16:00", "18:00", "20:00", "22:00"])
    min_lead_minutes = int(cfg.get("min_lead_minutes", 15))

    now_ist = from_dt_ist or datetime.datetime.now(IST_TZ)
    earliest_allowed_ist = now_ist + datetime.timedelta(minutes=min_lead_minutes)

    reserved_utc = get_already_reserved_utc_slots()
    assigned = []

    date_cursor = now_ist.date()
    max_days_lookahead = 30  # Safety boundary
    day_count = 0

    while len(assigned) < count and day_count < max_days_lookahead:
        for slot_str in daily_slots:
            parts = slot_str.strip().split(":")
            h, m = int(parts[0]), int(parts[1])

            slot_dt_ist = datetime.datetime(
                date_cursor.year,
                date_cursor.month,
                date_cursor.day,
                h,
                m,
                0,
                tzinfo=IST_TZ,
            )

            # Must be in the future (at least min_lead_minutes ahead)
            if slot_dt_ist <= earliest_allowed_ist:
                continue

            # Convert to UTC
            slot_dt_utc = slot_dt_ist.astimezone(datetime.timezone.utc)
            utc_iso = slot_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Check if this slot was already booked
            if utc_iso in reserved_utc:
                continue

            # Format 12-hour AM/PM string for human reading
            time_12h = slot_dt_ist.strftime("%I:%M %p")

            assigned.append({
                "slot_index": len(assigned) + 1,
                "date_ist": str(date_cursor),
                "time_ist": slot_str,
                "datetime_ist_display": f"{date_cursor.strftime('%b %d, %Y')} at {slot_str} IST ({time_12h})",
                "scheduled_for_utc": utc_iso,
                "slot_dt_ist": slot_dt_ist,
            })
            reserved_utc.add(utc_iso)

            if len(assigned) >= count:
                break

        date_cursor += datetime.timedelta(days=1)
        day_count += 1

    return assigned


def print_schedule_table(slots: list[dict]):
    print("=" * 80)
    print("📅 FIXED AWAKE-HOUR SCHEDULE ASSIGNMENT (IST -> UTC)")
    print("=" * 80)
    print(f"{'Clip #':<8}{'Date (IST)':<14}{'Time (IST)':<14}{'12-Hour IST':<16}{'Zernio scheduledFor (UTC)':<26}")
    print("-" * 80)
    for s in slots:
        cid = f"Clip #{s['slot_index']}"
        d_ist = s["date_ist"]
        t_ist = s["time_ist"] + " IST"
        t_12h = s["slot_dt_ist"].strftime("%I:%M %p")
        utc = s["scheduled_for_utc"]
        print(f"{cid:<8}{d_ist:<14}{t_ist:<14}{t_12h:<16}{utc:<26}")
    print("=" * 80)


def update_schedule_interactively(new_slots: list[str] = None, new_cap: int = None, notes: str = None) -> dict:
    cfg = load_schedule_config()
    if new_slots:
        cfg["daily_slots_ist"] = new_slots
    if new_cap:
        cfg["max_clips_per_day"] = new_cap
    if notes:
        cfg["notes"] = notes

    save_schedule_config(cfg)
    print("\n✅ Schedule configuration updated and locked in!")
    print(f"Timezone:         {cfg.get('timezone')}")
    print(f"Daily Slots (IST): {', '.join(cfg.get('daily_slots_ist', []))}")
    print(f"Daily Cap:        {cfg.get('max_clips_per_day')} clips/day")
    print(f"Notes:            {cfg.get('notes')}")
    return cfg


if __name__ == "__main__":
    slots = get_next_available_slots(12)
    print_schedule_table(slots)
