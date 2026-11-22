"""Campaign Brief & Rule Engine Manager.

Handles reading, updating, and validating the active Whop Content Rewards campaign rules.
"""

import datetime
import json
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import CAMPAIGN_PATH, load_active_campaign, save_active_campaign


def show_active_campaign():
    campaign = load_active_campaign()
    print("=" * 70)
    print("ACTIVE CAMPAIGN RULES")
    print("=" * 70)
    print(f"Campaign Name:         {campaign.get('campaign_name')}")
    print(f"Allowed Source:        {campaign.get('allowed_source')}")
    print(f"Required Caption Text: {campaign.get('required_caption_text')}")
    print(f"Required Channel Tag:  {campaign.get('required_channel_tag')}")
    print(f"Required Hashtags:     {', '.join(campaign.get('required_hashtags', []))}")
    print(f"Language:              {campaign.get('language')}")
    print(f"Quality Rules:         {campaign.get('quality_rules')}")
    print(f"Safety Filters:        {campaign.get('safety_filters')}")
    print(f"Watermark Path:        {campaign.get('watermark_path') or 'None'}")
    print(f"Last Updated:          {campaign.get('updated_at')}")
    print("=" * 70)
    return campaign


def update_campaign_from_dict(new_rules: dict):
    campaign = load_active_campaign()
    for k, v in new_rules.items():
        if v is not None:
            campaign[k] = v
    campaign["updated_at"] = datetime.datetime.now().astimezone().isoformat()
    save_active_campaign(campaign)
    print("\n✅ Campaign rules updated and locked in!")
    show_active_campaign()
    return campaign


def parse_campaign_brief(text: str) -> dict:
    """Parses free-form campaign text to extract key parameters."""
    rules = {}

    name_m = re.search(r"(?:campaign[ _]?name|name)[:=]\s*([^\n\r]+)", text, re.IGNORECASE)
    if name_m:
        rules["campaign_name"] = name_m.group(1).strip().strip("'\"")

    src_m = re.search(r"(?:allowed[ _]?source|source)[:=]\s*([^\n\r]+)", text, re.IGNORECASE)
    if src_m:
        rules["allowed_source"] = src_m.group(1).strip().strip("'\"")

    cap_m = re.search(r"(?:required[ _]?caption[ _]?text|caption[ _]?text|caption)[:=]\s*([^\n\r]+)", text, re.IGNORECASE)
    if cap_m:
        rules["required_caption_text"] = cap_m.group(1).strip().strip("'\"")

    tag_m = re.search(r"(?:required[ _]?channel[ _]?tag|channel[ _]?tag|tag)[:=]\s*([^\n\r]+)", text, re.IGNORECASE)
    if tag_m:
        rules["required_channel_tag"] = tag_m.group(1).strip().strip("'\"")

    tags = re.findall(r"#[A-Za-z0-9_]+", text)
    if tags:
        rules["required_hashtags"] = list(dict.fromkeys(tags))

    wm_m = re.search(r"(?:watermark[ _]?path|watermark)[:=]\s*([^\n\r]+)", text, re.IGNORECASE)
    if wm_m:
        wm_val = wm_m.group(1).strip().strip("'\"")
        rules["watermark_path"] = None if wm_val.lower() in ("null", "none", "") else wm_val

    return rules


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_active_campaign()
    else:
        show_active_campaign()
