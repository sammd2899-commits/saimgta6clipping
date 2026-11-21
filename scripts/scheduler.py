"""Awake-Hour Schedule Engine.

Converts local awake slots into UTC ISO 8601 strings for Zernio API v1.
"""

import datetime
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import CONFIG_DIR

SCHEDULE_PATH = CONFIG_DIR / "schedule_config.json"


def load_schedule_config() -> dict:
    if not SCHEDULE_PATH.exists():
        example_path = CONFIG_DIR / "schedule_config.example.json"
        if example_path.exists():
            with open(example_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "timezone": "Asia/Kolkata",
            "utc_offset_hours": 5.5,
            "daily_slots_ist": ["14:00", "16:00", "18:00", "20:00", "22:00"],
            "max_clips_per_day": 5,
            "min_lead_minutes": 15,
        }
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_schedule_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cfg["updated_at"] = datetime.datetime.now().astimezone().isoformat()
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def get_next_available_slots(count: int, start_from_utc: datetime.datetime = None) -> list[dict]:
    cfg = load_schedule_config()
    daily_slots = sorted(cfg.get("daily_slots_ist", ["14:00", "16:00", "18:00", "20:00", "22:00"]))
    offset_h = float(cfg.get("utc_offset_hours", 5.5))
    min_lead = int(cfg.get("min_lead_minutes", 15))

    tz_local = datetime.timezone(datetime.timedelta(hours=offset_h))
    now_utc = start_from_utc or datetime.datetime.now(datetime.timezone.utc)
    now_local = now_utc.astimezone(tz_local)
    min_allowed_local = now_local + datetime.timedelta(minutes=min_lead)

    allocated_slots = []
    day_cursor = now_local.date()

    while len(allocated_slots) < count:
        for slot_str in daily_slots:
            if len(allocated_slots) >= count:
                break
            hh, mm = map(int, slot_str.split(":"))
            slot_dt_local = datetime.datetime(
                day_cursor.year, day_cursor.month, day_cursor.day,
                hh, mm, 0, tzinfo=tz_local
            )
            if slot_dt_local > min_allowed_local:
                slot_dt_utc = slot_dt_local.astimezone(datetime.timezone.utc)
                allocated_slots.append({
                    "slot_index": len(allocated_slots) + 1,
                    "date_ist": day_cursor.isoformat(),
                    "time_ist": slot_str,
                    "datetime_ist_display": slot_dt_local.strftime("%Y-%m-%d %I:%M %p"),
                    "scheduled_for_utc": slot_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
        day_cursor += datetime.timedelta(days=1)

    return allocated_slots


def print_schedule_table(slots: list[dict]):
    print("=" * 80)
    print("CALCULATED POSTING SCHEDULE (LOCAL -> UTC)")
    print("=" * 80)
    print(f"{'Clip #':<8}{'Date':<14}{'Local Time':<14}{'12-Hour':<16}{'Zernio scheduledFor (UTC)'}")
    print("-" * 80)
    for s in slots:
        idx = s.get("slot_index", "")
        dt_disp = s.get("datetime_ist_display", "")
        utc_val = s.get("scheduled_for_utc", "")
        d_val = s.get("date_ist", "")
        t_val = s.get("time_ist", "")
        print(f"Clip #{idx:<2} {d_val:<14}{t_val:<14}{dt_disp:<16}{utc_val}")
    print("=" * 80)
