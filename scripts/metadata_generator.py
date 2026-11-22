"""Viral Metadata Generator with Platform Validators & Continuous Learning.

Strict Platform Rules:
- Instagram Reels:
  * Max 5 hashtags total (3 required campaign tags + max 2 extra tags)
  * 1 DM-share trigger line
  * Mandatory credit & channel tag (Watch the official livestream creator / @Creator)
  * Zero third-party watermarks
- YouTube Shorts:
  * English curiosity-gap title <= 65 characters including #Shorts
  * Full campaign credit + @Creator + description hashtags
  * Engaging English first comment
- Dynamic Campaign Support:
  * Overrides all campaign fields dynamically from config/active_campaign.json
"""

import json
import random
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    CONFIG_DIR,
    enforce_and_auto_append_compliance,
    load_active_campaign,
    load_learned_rules,
    load_viral_dna_weights,
)

EDITING_RULES_PATH = CONFIG_DIR / "editing_rules.json"


def load_platform_rules() -> dict:
    if EDITING_RULES_PATH.exists():
        with open(EDITING_RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("platform_metadata", {})
    return {}


DM_SHARE_TRIGGERS = [
    "Send this to your GTA duo 😭",
    "Tag the friend who drives like this",
    "Would you survive this chase? 👇",
    "Rate this escape 1–10 💀",
    "Share this with someone who needs to see GTA 6 physics 🏎️",
]

PINNED_COMMENTS = [
    "Would you have survived this in GTA 6? 😂 Drop your reaction below! 👇",
    "Rate this escape from 1 to 10! 🚔💨 What would you have done?",
    "Is GTA 6 police AI too overpowered or pure genius? Let me know! 💀",
    "Did you spot that detail in the background? 👀 Tell me what you saw!",
    "Who else is hyped for GTA 6 launch day? 🔥 Comment below!",
    "Best GTA 6 moment of the stream or what? Drop your thoughts! 🎮",
]


def generate_metadata_for_clip(clip_id: int, hook_text: str, campaign: dict = None) -> dict:
    """Generates strictly compliant platform metadata for Instagram Reels & YouTube Shorts."""
    if campaign is None:
        campaign = load_active_campaign()

    platform_cfg = load_platform_rules()
    ig_cfg = platform_cfg.get("instagram_reels", {})
    yt_cfg = platform_cfg.get("youtube_shorts", {})

    # Dynamic campaign overrides
    req_cap = campaign.get("required_caption_text")
    mandatory_credit = (req_cap if req_cap is not None else ig_cfg.get("mandatory_credit", "")).strip()

    req_chan = campaign.get("required_channel_tag")
    mandatory_channel_tag = (req_chan if req_chan is not None else ig_cfg.get("mandatory_channel_tag", "")).strip()

    required_campaign_tags = (
        campaign.get("required_hashtags")
        or ig_cfg.get("required_campaign_tags")
        or ["#GTA6", "#GTAVI"]
    )

    clean_hook = hook_text.replace("*", "").strip()

    # 1. YouTube Shorts Title: Enforce English Curiosity Gap <= 65 chars total (+ #Shorts)
    tag_shorts = "#Shorts"
    max_title_len = yt_cfg.get("title_max_chars", 65)
    max_hook_len = max_title_len - len(tag_shorts) - 1

    if len(clean_hook) <= max_hook_len:
        yt_title = f"{clean_hook} {tag_shorts}".strip()
    else:
        truncated_hook = clean_hook[:max_hook_len - 3].rstrip() + "..."
        yt_title = f"{truncated_hook} {tag_shorts}".strip()

    # Assert strictly <= 65 characters
    if len(yt_title) > max_title_len:
        yt_title = yt_title[:max_title_len]

    # 2. Instagram Reels Hashtags: Strictly max 5 total (required + up to extras)
    viral_weights = load_viral_dna_weights()
    learned_tags = viral_weights.get("hashtags_and_dm_triggers", {}).get("extra_hashtags_ranked")
    extra_tags_pool = learned_tags or ig_cfg.get("extra_tags_max_2", ["#GTAVI", "#GTA6Clips", "#GamingClips"])
    final_hashtags = list(required_campaign_tags)
    for extra in extra_tags_pool:
        if len(final_hashtags) >= 5:
            break
        if extra not in final_hashtags:
            final_hashtags.append(extra)
    final_hashtags = final_hashtags[:5]
    hashtags_str = " ".join(final_hashtags)

    # 3. Instagram Reels Caption (DM-share trigger at line 1, geo-signal, <= 5 hashtags)
    learned_dm_triggers = [
        t["trigger"] for t in viral_weights.get("hashtags_and_dm_triggers", {}).get("dm_triggers_ranked", [])
        if "trigger" in t
    ]
    triggers = learned_dm_triggers or ig_cfg.get("dm_share_triggers", DM_SHARE_TRIGGERS)
    dm_trigger = triggers[(clip_id - 1) % len(triggers)]
    location_signal = "📍 Miami, Florida (Vice City)"

    caption_parts = [f"{dm_trigger}", f"{clean_hook}\n{location_signal}"]
    credit_line = f"{mandatory_credit} {mandatory_channel_tag}".strip()
    if credit_line:
        caption_parts.append(f"{credit_line}!")
    caption_parts.append(hashtags_str)
    caption = "\n\n".join(caption_parts)

    # 4. Pinned / First Comment
    first_comment = PINNED_COMMENTS[(clip_id - 1) % len(PINNED_COMMENTS)]

    # 5. Hard Python Compliance Validator
    compliant_title, compliant_caption, modified = enforce_and_auto_append_compliance(
        yt_title, caption, campaign
    )

    return {
        "clip_id": clip_id,
        "title": compliant_title,
        "caption": compliant_caption,
        "first_comment": first_comment,
        "hashtags": final_hashtags,
        "total_hashtags": len(final_hashtags),
        "is_compliant": True,
        "mandatory_credit": mandatory_credit,
        "mandatory_channel_tag": mandatory_channel_tag,
    }


if __name__ == "__main__":
    meta = generate_metadata_for_clip(1, "GTA 6 NPCs are actually terrifying...")
    print(f"Title ({len(meta['title'])} chars): {meta['title']}")
    print(f"\nCaption:\n{meta['caption']}")
    print(f"\nHashtags ({meta['total_hashtags']}): {meta['hashtags']}")
    print(f"First Comment: {meta['first_comment']}")
