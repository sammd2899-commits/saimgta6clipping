"""Active Campaign Manager.

Allows viewing and updating Whop/Vyro Content Rewards campaign rules.
"""

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import load_active_campaign, save_active_campaign


def show_active_campaign():
    campaign = load_active_campaign()
    print("=" * 70)
    print("ACTIVE CAMPAIGN BRIEF & COMPLIANCE RULES")
    print("=" * 70)
    print(f"Campaign Name:    {campaign.get('campaign_name')}")
    print(f"Allowed Source:   {campaign.get('allowed_source')}")
    print(f"Required Caption: {campaign.get('required_caption_text')}")
    print(f"Channel Tag:      {campaign.get('required_channel_tag')}")
    print(f"Hashtags:         {' '.join(campaign.get('required_hashtags', []))}")
    print(f"Language:         {campaign.get('language')}")
    print(f"Quality Rules:    {campaign.get('quality_rules')}")
    print(f"Safety Filters:   {campaign.get('safety_filters')}")
    print(f"Last Updated:     {campaign.get('updated_at')}")
    print("=" * 70)


def update_campaign_from_dict(updates: dict):
    campaign = load_active_campaign()
    campaign.update(updates)
    save_active_campaign(campaign)
    print(f"✅ Campaign '{campaign.get('campaign_name')}' updated successfully.")
