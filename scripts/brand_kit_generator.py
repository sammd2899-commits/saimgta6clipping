"""Brand Kit & Profile Setup Guide Generator for Instagram & YouTube.

Generates channel names, handle ideas, bios, channel keywords, and compliant hashtags
using Google Gemini (or high-converting deterministic templates) and saves to config/brand_kit.md.
"""

import datetime
import json
import random
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import BASE_DIR, CONFIG_DIR
from gemini_backend import call_gemini, has_gemini_api_key

BRAND_KIT_MD_PATH = CONFIG_DIR / "brand_kit.md"

PLATFORM_GUIDES = {
    "instagram": {
        "title": "Instagram / Meta Professional Setup Guide",
        "steps": [
            "1. Switch to Professional Account: Go to Profile → Settings → Account type and tools → Switch to Professional (choose 'Creator' or 'Video Creator').",
            "2. Keep Account Public: Professional accounts must remain Public to ensure Reels are discoverable and eligible for algorithmic distribution.",
            "3. Likes & View Counts Visible: Go to Settings → Like and share counts → Toggle ON (Whop and sponsors require visible public metrics).",
            "4. Upload at Highest Quality: Go to Settings → Preferences → Data usage and media quality → Enable 'Upload at highest quality'.",
            "5. Link Facebook Page: Visit facebook.com on desktop → Page Settings → Linked accounts → Connect your Instagram account using your existing personal Facebook.",
            "6. Algorithmic Warm-up: Post 3–5 Reels/day spaced across peak IST hours (14:00, 18:00, 20:00, 22:00 IST) during your first 7 days.",
        ],
    },
    "youtube": {
        "title": "YouTube Studio Channel Setup Guide",
        "steps": [
            "1. Channel Name & Handle: Open studio.youtube.com → Customization → Basic info → Set your public Channel Name and @handle.",
            "2. Target Country: Open Settings → Channel → Basic info → Set Country of residence to 'United States' (crucial for Tier-1 US/UK/CA CPM payout eligibility).",
            "3. Default Audience: Settings → Channel → Advanced settings → Select 'No, set this channel as not made for kids'.",
            "4. Default Comments & Likes: Settings → Upload defaults → Advanced settings → Set Comments to 'On' and check 'Show how many viewers like this video'.",
            "5. Feature Eligibility (Tier-1 Unlock): Settings → Channel → Feature eligibility → Complete Standard, Intermediate (Phone verification), and Advanced features (Video ID / channel history) to unlock custom thumbnails and bypass daily Shorts upload limits.",
            "6. Channel Keywords: Settings → Channel → Basic info → Paste the generated channel keywords to index your channel for GTA 6 discovery.",
        ],
    },
}

TEMPLATE_NAME_PREFIXES = [
    "ViceCity", "GTA6", "Vice", "Leonida", "Rockstar", "Pulse", "Chaos", "Apex",
    "Prime", "Volt", "Drift", "Nitro", "Velocity", "Phantom", "Overdrive"
]

TEMPLATE_NAME_SUFFIXES = [
    "Clips", "Pulse", "Central", "Chaos", "Hub", "Daily", "Reels", "Vault",
    "HQ", "Zone", "Moments", "Arcade", "Glitch", "Speed", "Stunts"
]


def _generate_template_brand_kit(platform: str, base_name: str | None = None) -> dict:
    prefix = random.choice(TEMPLATE_NAME_PREFIXES)
    suffix = random.choice(TEMPLATE_NAME_SUFFIXES)
    brand_name = base_name if base_name else f"{prefix}{suffix}"

    slug_base = re.sub(r"[^a-zA-Z0-9]", "", brand_name).lower()
    handles = [
        f"@{slug_base}",
        f"@{slug_base}.gta6",
        f"@{slug_base}_official",
        f"@{slug_base}clips",
    ]

    if platform == "instagram":
        bio = (
            f"🌴 Daily GTA 6 chaos, wild NPC AI & physics glitches\n"
            f"🎮 Vice City highlights & best moments\n"
            f"👇 Watch full stream clips below"
        )
    else:
        bio = (
            f"Welcome to {brand_name}! We curate and post the most shocking, hilarious, "
            f"and high-energy GTA 6 Vice City gameplay moments, police escapes, physics glitches, "
            f"and crazy NPC AI encounters. Subscribe for daily 9:16 Shorts!"
        )

    keywords = [
        "GTA 6",
        "GTA VI",
        "Grand Theft Auto VI",
        "Vice City",
        "GTA 6 Gameplay",
        "GTA 6 Clips",
        "Rockstar Games",
        "GTA 6 Shorts",
    ]

    hashtags = ["#GTA6", "#GTAVI", "#ViceCity", "#GTA6Clips", "#Gaming"]

    return {
        "brand_name": brand_name,
        "handles": handles,
        "bio": bio,
        "keywords": keywords,
        "hashtags": hashtags,
    }


def generate_profile_kit(
    platform: str = "instagram",
    brand_name: str | None = None,
    niche: str = "GTA 6 / Gaming",
) -> dict:
    """Generates a unique profile kit and writes it to config/brand_kit.md."""
    platform_key = "youtube" if "you" in platform.lower() else "instagram"
    data = None

    if has_gemini_api_key():
        prompt = (
            f"Act as a professional social media branding expert for a Tier-1 {niche} clipping channel.\n"
            f"Target Platform: {platform_key.upper()}.\n"
            f"{'Base Brand Name: ' + brand_name if brand_name else 'Generate a brand-new punchy, memorable, short 1-2 word channel name'}.\n\n"
            f"Output strictly valid JSON with these exact keys:\n"
            f"1. \"brand_name\": short punchy brand name (e.g. ViceCityPulse, GTA6ChaosCentral)\n"
            f"2. \"handles\": list of 4 clean @handles\n"
            f"3. \"bio\": high-converting bio (max 150 chars for Instagram with emojis, or 250 chars for YouTube Shorts)\n"
            f"4. \"keywords\": list of 6-8 SEO channel search keywords\n"
            f"5. \"hashtags\": list of exactly 5 viral hashtags (strictly <= 5 hashtags)\n"
            f"Return JSON only, no markdown ticks, no extra text."
        )
        try:
            raw_text = call_gemini(
                prompt=prompt,
                system_instruction="You are an expert social media growth strategist specializing in short-form gaming video algorithms.",
                temperature=0.8,
            )
            if raw_text:
                clean_json = raw_text.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
                    clean_json = re.sub(r"\s*```$", "", clean_json)
                parsed = json.loads(clean_json)
                if "brand_name" in parsed and "handles" in parsed and "bio" in parsed:
                    data = {
                        "brand_name": str(parsed.get("brand_name", "")).strip(),
                        "handles": [str(h) for h in parsed.get("handles", [])][:4],
                        "bio": str(parsed.get("bio", "")).strip(),
                        "keywords": [str(k) for k in parsed.get("keywords", [])][:8],
                        "hashtags": [str(t) for t in parsed.get("hashtags", [])][:5],
                    }
        except Exception as e:
            print(f"[Brand Kit Generator] Gemini generation notice: {e}")

    if not data:
        data = _generate_template_brand_kit(platform_key, brand_name)

    # Attach setup guide
    guide_info = PLATFORM_GUIDES.get(platform_key, PLATFORM_GUIDES["instagram"])
    data["platform"] = platform_key
    data["guide_title"] = guide_info["title"]
    data["guide_steps"] = guide_info["steps"]

    # Save to config/brand_kit.md
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    now_str = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    md_content = f"""# 🎮 SaimClip Studio Brand & Profile Kit
Generated on: {now_str}
Platform Target: {platform_key.capitalize()}

---

## 📌 Brand Identity
- **Channel / Brand Name:** `{data['brand_name']}`
- **Suggested Handles:**
{chr(10).join([f"  - `{h}`" for h in data['handles']])}

## 📝 Profile Bio / Description
```text
{data['bio']}
```

## 🏷️ Channel Keywords
`{', '.join(data['keywords'])}`

## #️⃣ Default Hashtags (≤ 5 tags)
`{' '.join(data['hashtags'])}`

---

## 📋 Platform Setup Checklist ({guide_info['title']})
{chr(10).join(guide_info['steps'])}
"""
    BRAND_KIT_MD_PATH.write_text(md_content, encoding="utf-8")
    data["saved_to"] = "config/brand_kit.md"
    return data
