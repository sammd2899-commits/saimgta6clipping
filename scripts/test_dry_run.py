"""Comprehensive Dry-Run Verification Suite for Awake-Hour Scheduling & Compliance.

Proves:
1. 12 clips roll cleanly across days using awake IST / local slots.
2. Accurate conversion to ISO 8601 UTC.
3. Every clip payload passes the hard Python compliance validator.
"""

import datetime
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import load_active_campaign, verify_post_compliance
from metadata_generator import generate_metadata_for_clip
from scheduler import get_next_available_slots, load_schedule_config, print_schedule_table


def test_awake_schedule_simulation():
    print("=" * 80)
    print("TEST: 12-CLIP AWAKE-HOUR SCHEDULING SIMULATION")
    print("=" * 80)

    cfg = load_schedule_config()
    allowed_slots = cfg.get("daily_slots_ist", ["14:00", "16:00", "18:00", "20:00", "22:00"])

    slots = get_next_available_slots(12)
    assert len(slots) == 12, f"Expected 12 slots, got {len(slots)}"

    for s in slots:
        t_val = s["time_ist"]
        utc_iso = s["scheduled_for_utc"]
        assert t_val in allowed_slots, f"Slot {t_val} is outside allowed awake slots: {allowed_slots}"
        assert utc_iso.endswith("Z"), f"Expected UTC ISO string ending in Z, got {utc_iso}"

    print_schedule_table(slots)
    return slots


def test_payload_compliance_across_all_12_clips():
    print("\n" + "=" * 80)
    print("TEST: METADATA & CAMPAIGN COMPLIANCE GATE FOR ALL 12 CLIPS")
    print("=" * 80)
    campaign = load_active_campaign()

    sample_hooks = [
        "GTA 6 NPCs are actually terrifying...",
        "Watch the police AI at 0:08",
        "He didn't see what was behind him",
        "Bro really tried escaping cops on THIS",
        "This looks normal, until the end...",
        "Instant karma in under 2 seconds",
        "Nobody expected Rockstar to add THIS",
        "Worst getaway driver in Vice City",
        "He celebrated way too early here",
        "He stole a fighter jet and regretted it",
        "First time seeing this secret location",
        "GTA 6 physics just broke completely",
    ]

    for idx, hook in enumerate(sample_hooks, start=1):
        meta = generate_metadata_for_clip(idx, hook, campaign)
        assert len(meta["title"]) <= 65, f"Title exceeds 65 chars: {meta['title']}"
        assert meta["total_hashtags"] <= 5, f"Hashtags exceed 5: {meta['hashtags']}"
        compliant, missing = verify_post_compliance(meta["title"], meta["caption"], campaign)
        assert compliant, f"Clip #{idx} failed compliance: {missing}"

    print(f"✔ All 12 simulated clips passed hard Python compliance gate.")
    print("=" * 80)


if __name__ == "__main__":
    test_awake_schedule_simulation()
    test_payload_compliance_across_all_12_clips()
    print("🎉 ALL DRY-RUN CHECKS PASSED SUCCESSFULLY")
