"""Configuration, Campaign Rule & Continuous Learning Manager.

Fully dynamic and self-contained: resolves all paths relative to repository root.
"""

import datetime
import json
import os
import re
import shutil
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
SCRIPTS_DIR = BASE_DIR / "scripts"
STATE_DIR = BASE_DIR / "state"
MEMORY_DIR = BASE_DIR / "memory"
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

ENV_PATH = BASE_DIR / ".env"
CAMPAIGN_PATH = CONFIG_DIR / "active_campaign.json"
ACCOUNTS_PATH = CONFIG_DIR / "zernio_accounts.json"
QUEUE_PATH = STATE_DIR / "job_queue.json"
LEARNED_RULES_PATH = MEMORY_DIR / "learned_rules.md"
PERF_LOG_PATH = MEMORY_DIR / "performance_log.json"
PUBLISHED_JSON = LOGS_DIR / "published_clips.json"
PUBLISHED_CSV = LOGS_DIR / "published_clips.csv"
EDITING_RULES_PATH = CONFIG_DIR / "editing_rules.json"

# Resolve tools dynamically
def get_ytdlp_cmd() -> list[str]:
    """Finds yt-dlp executable or returns module execution."""
    which_ytdlp = shutil.which("yt-dlp")
    if which_ytdlp:
        return [which_ytdlp]
    fallback_venv = Path.home() / ".beyondgtaclips" / "venv" / "Scripts" / "yt-dlp.exe"
    if fallback_venv.exists():
        return [str(fallback_venv)]
    return [sys.executable, "-m", "yt_dlp"]


def get_python_exe() -> str:
    return sys.executable


FFMPEG_EXE = "ffmpeg"


def load_env() -> dict:
    env_vars = {}
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip().strip("'\"")
    return env_vars


def get_zernio_api_key() -> str:
    env_vars = load_env()
    key = env_vars.get("ZERNIO_API_KEY") or os.environ.get("ZERNIO_API_KEY")
    if not key:
        raise ValueError("ZERNIO_API_KEY not configured. Set it in .env or run 'python scripts/bootstrap.py'")
    return key


def get_post_interval_hours() -> float:
    env_vars = load_env()
    val = env_vars.get("POST_INTERVAL_HOURS")
    try:
        return float(val) if val else 2.0
    except ValueError:
        return 2.0


def load_active_campaign() -> dict:
    if not CAMPAIGN_PATH.exists():
        example_path = CONFIG_DIR / "active_campaign.example.json"
        if example_path.exists():
            with open(example_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "campaign_name": "Default Campaign",
            "required_caption_text": "Watch official livestream",
            "required_channel_tag": "@Creator",
            "required_hashtags": ["#GTA6", "#GrandTheftAutoVI"],
        }
    with open(CAMPAIGN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_active_campaign(campaign_data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CAMPAIGN_PATH, "w", encoding="utf-8") as f:
        json.dump(campaign_data, f, indent=2)


def load_zernio_accounts() -> dict:
    if not ACCOUNTS_PATH.exists():
        example_path = CONFIG_DIR / "zernio_accounts.example.json"
        if example_path.exists():
            with open(example_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    with open(ACCOUNTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_zernio_accounts(accounts_data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACCOUNTS_PATH, "w", encoding="utf-8") as f:
        json.dump(accounts_data, f, indent=2)


def load_job_queue() -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not QUEUE_PATH.exists():
        initial = {
            "source_url": None,
            "video_title": None,
            "created_at": None,
            "last_updated": None,
            "clips": [],
        }
        save_job_queue(initial)
        return initial
    with open(QUEUE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_job_queue(queue_data: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    queue_data["last_updated"] = datetime.datetime.now().astimezone().isoformat()
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2)


def load_learned_rules() -> str:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not LEARNED_RULES_PATH.exists():
        template_path = MEMORY_DIR / "learned_rules.template.md"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        return ""
    with open(LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
        return f.read()


def append_learned_rule(category: str, rule_text: str):
    """Appends a verified continuous learning directive."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    new_entry = f"\n- **{category} ({timestamp}):** {rule_text.strip()}"
    with open(LEARNED_RULES_PATH, "a", encoding="utf-8") as f:
        f.write(new_entry)


def verify_post_compliance(title: str, caption: str, campaign: dict = None) -> tuple[bool, list[str]]:
    """Checks whether text conforms to platform constraints and campaign rules."""
    if campaign is None:
        campaign = load_active_campaign()

    missing = []
    if len(title) > 65:
        missing.append(f"Title exceeds 65 characters ({len(title)} chars)")

    req_caption = campaign.get("required_caption_text", "").strip()
    req_tag = campaign.get("required_channel_tag", "").strip()
    req_hashtags = campaign.get("required_hashtags", [])

    full_text = f"{title} {caption}"

    if req_caption and req_caption.lower() not in full_text.lower():
        missing.append(f"required_caption_text missing: '{req_caption}'")

    if req_tag and req_tag.lower() not in full_text.lower():
        missing.append(f"required_channel_tag missing: '{req_tag}'")

    for tag in req_hashtags:
        tag_clean = tag.strip().lower()
        if tag_clean and tag_clean not in full_text.lower():
            missing.append(f"required_hashtag missing: '{tag}'")

    found_tags = re.findall(r"#\w+", caption)
    if len(found_tags) > 5:
        missing.append(f"Too many hashtags ({len(found_tags)} > 5 max for Instagram Reels)")

    is_compliant = len(missing) == 0
    return is_compliant, missing


def enforce_and_auto_append_compliance(title: str, caption: str, campaign: dict = None) -> tuple[str, str, bool]:
    """Guarantees zero-dropped-tag compliance by appending missing elements and truncating title/hashtags."""
    if campaign is None:
        campaign = load_active_campaign()

    modified = False

    # 1. Enforce title length <= 65 chars
    clean_title = title.strip()
    if len(clean_title) > 65:
        tag = "#Shorts" if "#Shorts" in clean_title else ""
        base = clean_title.replace(tag, "").strip()
        avail = 65 - len(tag) - 1
        base = base[:avail - 3].rstrip() + "..."
        clean_title = f"{base} {tag}".strip()
        modified = True

    # 2. Check required campaign elements
    req_caption = campaign.get("required_caption_text", "").strip()
    req_tag = campaign.get("required_channel_tag", "").strip()
    req_hashtags = campaign.get("required_hashtags", [])

    full_text = f"{clean_title} {caption}"
    append_blocks = []

    if req_caption and req_caption.lower() not in full_text.lower():
        append_blocks.append(req_caption)
        modified = True

    if req_tag and req_tag.lower() not in full_text.lower():
        append_blocks.append(req_tag)
        modified = True

    missing_hashtags = []
    for tag in req_hashtags:
        if tag.strip().lower() not in full_text.lower():
            missing_hashtags.append(tag.strip())
            modified = True

    if missing_hashtags:
        append_blocks.append(" ".join(missing_hashtags))

    compliant_caption = caption.strip()
    if append_blocks:
        compliant_caption += "\n\n" + "\n".join(append_blocks)

    # 3. Enforce max 5 hashtags
    all_tags = re.findall(r"#\w+", compliant_caption)
    if len(all_tags) > 5:
        kept_tags = []
        for r_tag in req_hashtags:
            if r_tag in all_tags and r_tag not in kept_tags:
                kept_tags.append(r_tag)
        for t in all_tags:
            if len(kept_tags) >= 5:
                break
            if t not in kept_tags:
                kept_tags.append(t)

        for t in all_tags:
            if t not in kept_tags:
                compliant_caption = re.sub(rf"{re.escape(t)}\b", "", compliant_caption)
        compliant_caption = re.sub(r"\n\s*\n\s*\n+", "\n\n", compliant_caption).strip()
        modified = True

    return clean_title, compliant_caption, modified
