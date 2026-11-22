"""Comprehensive Dry-Run Verification Suite for Fixed Awake-Hour IST Scheduling.

Proves:
1. 12 clips roll cleanly across days using ONLY 14:00, 16:00, 18:00, 20:00, 22:00 IST.
2. Exact conversion to ISO 8601 UTC (14:00 IST -> 08:30:00Z, etc.).
3. Every clip payload passes the hard Python compliance validator.
4. Output prints the clean IST dry-run schedule table.
"""

import datetime
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    load_active_campaign,
    verify_post_compliance,
)
from metadata_generator import generate_metadata_for_clip
from scheduler import get_next_available_slots, load_schedule_config, print_schedule_table


def test_ist_awake_schedule_simulation():
    print("=" * 80)
    print("TEST: 12-CLIP FIXED AWAKE-HOUR IST SCHEDULING SIMULATION (5 CLIPS/DAY)")
    print("=" * 80)

    cfg = load_schedule_config()
    allowed_slots = cfg.get("daily_slots_ist", ["14:00", "16:00", "18:00", "20:00", "22:00"])

    # 1. Fetch next 12 available slots
    slots = get_next_available_slots(12)
    assert len(slots) == 12, f"Expected 12 slots, got {len(slots)}"

    # 2. Verify all slots conform to awake IST times and accurate UTC conversion
    utc_mapping = {
        "14:00": "08:30:00Z",
        "16:00": "10:30:00Z",
        "18:00": "12:30:00Z",
        "20:00": "14:30:00Z",
        "22:00": "16:30:00Z",
    }

    day_distribution = {}

    for s in slots:
        t_ist = s["time_ist"]
        utc_iso = s["scheduled_for_utc"]
        d_ist = s["date_ist"]

        # Check allowed IST slots
        assert t_ist in allowed_slots, f"Slot {t_ist} is outside allowed awake slots: {allowed_slots}"

        # Check exact UTC mapping
        expected_utc_time = utc_mapping[t_ist]
        assert utc_iso.endswith(expected_utc_time), f"For IST {t_ist}, expected UTC {expected_utc_time}, got {utc_iso}"

        # Track daily distribution
        day_distribution[d_ist] = day_distribution.get(d_ist, 0) + 1

    print("\n✔ All 12 slots adhere strictly to awake IST times (zero overnight posts).")
    print("✔ UTC conversion verified (14:00 IST -> 08:30:00Z, 16:00 IST -> 10:30:00Z, etc.).")
    print(f"✔ Daily Roll-Over Distribution: {day_distribution}")
    for day, count in day_distribution.items():
        assert count <= 5, f"Day {day} exceeded max 5 clips/day cap: {count}"

    # 3. Print IST schedule table
    print()
    print_schedule_table(slots)
    return slots


def test_payload_compliance_across_all_12_clips():
    print("\n" + "=" * 80)
    print("TEST: METADATA & CAMPAIGN COMPLIANCE GATE FOR ALL 12 CLIPS")
    print("=" * 80)
    campaign = load_active_campaign()

    sample_hooks = [
        "KreekCraft just found the *CRAZIEST GLITCH* in GTA 6 😭",
        "This GTA 6 police chase got *COMPLETELY OUT OF HAND* 💀",
        "Nobody expected THIS to happen in GTA 6 🤯",
        "KreekCraft's reaction to this GTA 6 fail is *PRICELESS* 😂",
        "Rockstar definitely didn't plan for THIS GTA 6 moment 🚔",
        "Is this the *HARDEST MISSION* in GTA 6? 💥",
        "KreekCraft discovers an *INSANE SECRET* in GTA 6 🗺️",
        "Wait until you see how this GTA 6 chase ends 🚨",
        "The GTA 6 physics just *BROKE COMPLETELY* 😭",
        "KreekCraft gets *SURPRISED* by wild GTA 6 NPC chaos 🌴",
        "You won't believe this GTA 6 escape move 🏎️💨",
        "GTA 6 graphics and chaos are *NEXT LEVEL* 🔥",
    ]

    for idx, hook in enumerate(sample_hooks, start=1):
        meta = generate_metadata_for_clip(idx, hook, campaign)

        # Assert title constraints
        assert len(meta["title"]) <= 80, f"Clip #{idx} title exceeds 80 chars ({len(meta['title'])})"

        # Assert mandatory campaign texts
        is_compliant, missing = verify_post_compliance(meta["title"], meta["caption"], campaign)
        assert is_compliant, f"Clip #{idx} failed compliance gate: {missing}"

        assert campaign["required_caption_text"] in meta["caption"]
        assert campaign["required_channel_tag"] in meta["caption"]
        for tag in campaign["required_hashtags"]:
            assert tag in meta["caption"]

        assert meta["first_comment"], f"Clip #{idx} missing first comment"

    print("✔ All 12 simulated clips passed hard Python compliance gate:")
    print(f"  • Required Caption: '{campaign['required_caption_text']}'")
    print(f"  • Channel Tag:      '{campaign['required_channel_tag']}'")
    print(f"  • Hashtags:         {', '.join(campaign['required_hashtags'])}")
    print("  • Pinned Comment:   Included for all 12 clips")
    print("  • Title Length:     Strictly < 80 characters for all 12 clips")


if __name__ == "__main__":
    test_ist_awake_schedule_simulation()
    test_payload_compliance_across_all_12_clips()
    print("\n" + "=" * 80)
    print("🎉 ALL DRY-RUN CHECKS PASSED — 12 CLIPS READY FOR IST AWAKE SCHEDULING")
    print("=" * 80)
