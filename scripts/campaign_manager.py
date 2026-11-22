"""Campaign Brief, Rule Engine & Preset Library Manager.

Features:
- Reads and updates the active Whop Content Rewards campaign rules.
- Saves every updated brief as a reusable preset at config/presets/<campaign_slug>.json.
- Switches active campaign instantly between presets without manual JSON editing.
- Formats clean preset listings for CLI and chat commands.
"""

import datetime
import json
import re
import shutil
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    CAMPAIGN_PATH,
    CONFIG_DIR,
    PRESETS_DIR,
    load_active_campaign,
    save_active_campaign,
)


def slugify_campaign_name(name: str) -> str:
    """Converts a human-readable campaign name into a safe filename slug."""
    clean = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower()).strip("_")
    return clean or "custom_campaign"


def list_campaign_presets() -> list[dict]:
    """Lists all available campaign presets stored in config/presets/."""
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    preset_files = sorted(PRESETS_DIR.glob("*.json"))
    presets = []

    active = load_active_campaign()
    active_slug = active.get("campaign_slug") or slugify_campaign_name(active.get("campaign_name", ""))

    for idx, pf in enumerate(preset_files, 1):
        try:
            with open(pf, "r", encoding="utf-8") as f:
                data = json.load(f)
            slug = data.get("campaign_slug") or pf.stem
            is_active = (slug == active_slug or data.get("campaign_name") == active.get("campaign_name"))
            presets.append({
                "index": idx,
                "slug": slug,
                "path": pf,
                "data": data,
                "is_active": is_active,
            })
        except Exception as e:
            print(f"[Campaign Manager] Warning: Could not read preset {pf.name}: {e}")

    return presets


def print_presets_table(presets: list[dict] = None) -> list[dict]:
    if presets is None:
        presets = list_campaign_presets()

    print("=" * 75)
    print("📁 SAVED CAMPAIGN PRESET LIBRARY (config/presets/)")
    print("=" * 75)

    if not presets:
        print("No presets found in config/presets/. Add one via 'update campaign'.")
        print("=" * 75)
        return []

    for p in presets:
        idx = p["index"]
        d = p["data"]
        name = d.get("campaign_name", "Unnamed Campaign")
        slug = p["slug"]
        tags = " ".join(d.get("required_hashtags", []))
        cap = d.get("required_caption_text") or "None"
        tag = d.get("required_channel_tag") or "None"
        ret = d.get("min_post_retention_days", 60)
        active_tag = "  [ACTIVE]" if p["is_active"] else ""

        print(f"[#{idx}] {name}{active_tag}")
        print(f"     • Slug:         {slug}")
        print(f"     • Hashtags:     {tags}")
        print(f"     • Attribution:  {cap} ({tag})")
        print(f"     • Retention:    {ret} days minimum | Tier-1 payout rule enabled")
        print(f"     • Preset File:  config/presets/{p['path'].name}")
        print()

    print("-" * 75)
    print("👉 To switch preset: run 'python main.py --switch-campaign <SLUG_OR_#>'")
    print("   or say 'switch campaign' in chat.")
    print("=" * 75)
    return presets


def save_campaign_preset(campaign_data: dict, slug: str = None) -> Path:
    """Saves a campaign dictionary as a reusable preset and updates active_campaign.json."""
    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    if not slug:
        slug = campaign_data.get("campaign_slug") or slugify_campaign_name(campaign_data.get("campaign_name", "custom"))
    campaign_data["campaign_slug"] = slug
    campaign_data["updated_at"] = datetime.datetime.now().astimezone().isoformat()

    preset_path = PRESETS_DIR / f"{slug}.json"
    with open(preset_path, "w", encoding="utf-8") as f:
        json.dump(campaign_data, f, indent=2)

    # Also update active_campaign.json
    save_active_campaign(campaign_data)
    print(f"  ✔ Saved reusable preset: config/presets/{slug}.json")
    print(f"  ✔ Locked as active campaign: config/active_campaign.json")
    return preset_path


def switch_campaign_preset(selector: str | int) -> dict:
    """Switches the active campaign to a specified preset by index or slug."""
    presets = list_campaign_presets()
    if not presets:
        raise FileNotFoundError("No campaign presets found in config/presets/.")

    selected = None
    # 1. Try index match (e.g. 1 or '1')
    try:
        idx = int(selector)
        for p in presets:
            if p["index"] == idx:
                selected = p
                break
    except ValueError:
        pass

    # 2. Try slug or name match
    if not selected:
        sel_lower = str(selector).strip().lower()
        for p in presets:
            if p["slug"].lower() == sel_lower:
                selected = p
                break
            if p["data"].get("campaign_name", "").lower() == sel_lower:
                selected = p
                break

    if not selected:
        valid_options = ", ".join([f"#{p['index']} ({p['slug']})" for p in presets])
        raise ValueError(f"Preset '{selector}' not found. Available presets: {valid_options}")

    target_data = selected["data"]
    target_data["campaign_slug"] = selected["slug"]
    save_active_campaign(target_data)

    print("\n" + "=" * 75)
    print(f"✅ ACTIVATED CAMPAIGN PRESET: '{target_data.get('campaign_name')}'")
    print(f"   Slug:         {selected['slug']}")
    print(f"   Required:     {' '.join(target_data.get('required_hashtags', []))} | {target_data.get('required_caption_text')}")
    print(f"   Active File:  config/active_campaign.json")
    print("=" * 75)
    return target_data


def show_active_campaign() -> dict:
    campaign = load_active_campaign()
    print("=" * 75)
    print("ACTIVE CAMPAIGN RULES (config/active_campaign.json)")
    print("=" * 75)
    print(f"Campaign Name:         {campaign.get('campaign_name')}")
    print(f"Preset Slug:           {campaign.get('campaign_slug', 'custom')}")
    print(f"Allowed Source:        {campaign.get('allowed_source')}")
    print(f"Required Caption Text: {campaign.get('required_caption_text')}")
    print(f"Required Channel Tag:  {campaign.get('required_channel_tag')}")
    print(f"Required Hashtags:     {', '.join(campaign.get('required_hashtags', []))}")
    print(f"Language:              {campaign.get('language', 'en-US (Tier-1 US/UK/CA/AU)')}")
    print(f"Quality Rules:         {campaign.get('quality_rules')}")
    print(f"Safety Filters:        {campaign.get('safety_filters')}")
    print(f"Watermark Path:        {campaign.get('watermark_path') or 'None'}")
    print(f"Min Post Retention:    {campaign.get('min_post_retention_days', 60)} days")
    print(f"Tier-1 Payout Rule:    {campaign.get('tier1_only_payout')}")
    print(f"Last Updated:          {campaign.get('updated_at')}")
    print("=" * 75)
    return campaign


def update_campaign_from_dict(new_rules: dict) -> dict:
    campaign = load_active_campaign()
    for k, v in new_rules.items():
        if v is not None:
            campaign[k] = v

    slug = campaign.get("campaign_slug") or slugify_campaign_name(campaign.get("campaign_name", "custom"))
    save_campaign_preset(campaign, slug=slug)
    print("\n✅ Campaign rules updated and locked in as active + preset!")
    show_active_campaign()
    return campaign


def parse_campaign_brief(text: str) -> dict:
    """Parses free-form campaign text to extract key parameters and save as preset."""
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

    wm_m = re.search(r"(?:watermark[ _]?path|watermark|logo)[:=]\s*([^\n\r]+)", text, re.IGNORECASE)
    if wm_m:
        wm_val = wm_m.group(1).strip().strip("'\"")
        rules["watermark_path"] = None if wm_val.lower() in ("null", "none", "") else wm_val

    ret_m = re.search(r"(?:retention|days|min[ _]?days)[:=]?\s*(\d+)", text, re.IGNORECASE)
    if ret_m:
        rules["min_post_retention_days"] = int(ret_m.group(1))

    return rules


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list-presets":
            print_presets_table()
        elif sys.argv[1] == "--switch" and len(sys.argv) > 2:
            switch_campaign_preset(sys.argv[2])
        elif sys.argv[1] == "--show":
            show_active_campaign()
        else:
            show_active_campaign()
    else:
        show_active_campaign()
