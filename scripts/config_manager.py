"""Configuration, Campaign Rule & Continuous Learning Manager.

Fully dynamic and self-contained: resolves all paths relative to repository root.
Compatible across Windows, macOS, and Linux without hardcoded personal user paths.
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
ASSETS_DIR = BASE_DIR / "assets"

ENV_PATH = BASE_DIR / ".env"
CAMPAIGN_PATH = CONFIG_DIR / "active_campaign.json"
ACCOUNTS_PATH = CONFIG_DIR / "zernio_accounts.json"
QUEUE_PATH = STATE_DIR / "job_queue.json"
LEARNED_RULES_PATH = MEMORY_DIR / "learned_rules.md"
PERF_LOG_PATH = MEMORY_DIR / "performance_log.json"
VIRAL_DNA_PATH = MEMORY_DIR / "viral_dna_weights.json"
PUBLISHED_JSON = LOGS_DIR / "published_clips.json"
PUBLISHED_CSV = LOGS_DIR / "published_clips.csv"
EDITING_RULES_PATH = CONFIG_DIR / "editing_rules.json"


def get_ytdlp_exe() -> str:
    """Finds yt-dlp executable dynamically or returns executable command."""
    which_ytdlp = shutil.which("yt-dlp")
    if which_ytdlp:
        return which_ytdlp
    # Common cross-platform venv locations
    for p in [
        Path.home() / ".beyondgtaclips" / "venv" / "Scripts" / "yt-dlp.exe",
        Path.home() / ".beyondgtaclips" / "venv" / "bin" / "yt-dlp",
        BASE_DIR / ".venv" / "Scripts" / "yt-dlp.exe",
        BASE_DIR / ".venv" / "bin" / "yt-dlp",
    ]:
        if p.exists():
            return str(p)
    return "yt-dlp"


def get_ytdlp_cmd() -> list[str]:
    """Finds yt-dlp executable or returns python -m yt_dlp fallback."""
    exe = get_ytdlp_exe()
    if exe and shutil.which(exe):
        return [exe]
    return [sys.executable, "-m", "yt_dlp"]


def get_python_exe() -> str:
    return sys.executable


def get_models_dir() -> Path:
    """Returns local models cache directory (portable across user environments)."""
    p = Path.home() / ".beyondgtaclips" / "models" / "whisper"
    if p.exists():
        return p
    return BASE_DIR / "models" / "whisper"


# Compatibility aliases
YTDLP_EXE = get_ytdlp_exe()
PYTHON_EXE = get_python_exe()
FFMPEG_EXE = "ffmpeg"


def load_env() -> dict:
    env_vars = {}
    if not ENV_PATH.exists():
        return env_vars
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()
    return env_vars


def get_zernio_api_key() -> str:
    env_vars = load_env()
    key = env_vars.get("ZERNIO_API_KEY") or os.environ.get("ZERNIO_API_KEY")
    if not key:
        raise ValueError(
            "ZERNIO_API_KEY not configured. Set it in .env or run 'python scripts/bootstrap.py --key <YOUR_KEY>'"
        )
    return key


def get_post_interval_hours() -> float:
    env_vars = load_env()
    val = env_vars.get("POST_INTERVAL_HOURS") or os.environ.get("POST_INTERVAL_HOURS", "2.0")
    try:
        return float(val)
    except ValueError:
        return 2.0


def load_active_campaign() -> dict:
    if CAMPAIGN_PATH.exists():
        with open(CAMPAIGN_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    example_path = CONFIG_DIR / "active_campaign.example.json"
    if example_path.exists():
        with open(example_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "campaign_name": "Default Campaign",
        "required_caption_text": "Watch the official livestream creator",
        "required_channel_tag": "@Creator",
        "required_hashtags": ["#GTA6", "#GTAVI"],
        "watermark_path": None,
    }


def save_active_campaign(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CAMPAIGN_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_zernio_accounts() -> dict:
    if ACCOUNTS_PATH.exists():
        with open(ACCOUNTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    example_path = CONFIG_DIR / "zernio_accounts.example.json"
    if example_path.exists():
        with open(example_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"accounts": []}


def save_zernio_accounts(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACCOUNTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_job_queue() -> dict:
    if not QUEUE_PATH.exists():
        return {"source_url": None, "total_clips": 0, "clips": []}
    try:
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"source_url": None, "total_clips": 0, "clips": []}


def save_job_queue(queue_data: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    queue_data["last_updated"] = datetime.datetime.now().astimezone().isoformat()
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2)


def load_learned_rules() -> str:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if LEARNED_RULES_PATH.exists():
        with open(LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
            return f.read()

    template_path = MEMORY_DIR / "learned_rules.template.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")

    return ""


def load_viral_dna_weights() -> dict:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if VIRAL_DNA_PATH.exists():
        try:
            with open(VIRAL_DNA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    template_path = MEMORY_DIR / "viral_dna_weights.template.json"
    if template_path.exists():
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {}


def save_viral_dna_weights(weights: dict):
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(VIRAL_DNA_PATH, "w", encoding="utf-8") as f:
        json.dump(weights, f, indent=2)


def append_learned_rule(category: str, rule_text: str):
    """Appends a new verified rule to memory/learned_rules.md."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    new_entry = f"\n- **{category} ({timestamp}):** {rule_text.strip()}"
    with open(LEARNED_RULES_PATH, "a", encoding="utf-8") as f:
        f.write(new_entry)
    print(f"[Continuous Learning] Logged new rule to memory/learned_rules.md: {rule_text}")


def verify_post_compliance(title: str, caption: str, campaign: dict = None) -> tuple[bool, list[str]]:
    """Checks whether the generated text contains all mandatory campaign elements."""
    if campaign is None:
        campaign = load_active_campaign()

    missing = []
    if len(title) > 65:
        missing.append(f"Title too long ({len(title)} chars > 65 chars maximum)")

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

    # Enforce max 5 hashtags
    found_tags = re.findall(r"#\w+", caption)
    if len(found_tags) > 5:
        missing.append(f"Too many hashtags ({len(found_tags)} > 5 maximum for Instagram Reels)")

    is_compliant = len(missing) == 0
    return is_compliant, missing


def enforce_and_auto_append_compliance(title: str, caption: str, campaign: dict = None) -> tuple[str, str, bool]:
    """Hard Python Compliance Gate (Zero Dropped Tags Guarantee):

    Asserts compliance. Enforces title <= 65 chars and max 5 hashtags total.
    If any required tag or caption text is missing, automatically appends it.
    Returns: (title, compliant_caption, was_modified)
    """
    if campaign is None:
        campaign = load_active_campaign()

    modified = False

    # 1. Enforce title length <= 65 chars
    clean_title = title.strip()
    if len(clean_title) > 65:
        tag = "#Shorts" if "#Shorts" in clean_title else ""
        allowed_base = 65 - len(tag) - 1
        base = clean_title.replace(tag, "").strip()[:allowed_base].rstrip()
        clean_title = f"{base} {tag}".strip()
        modified = True

    req_caption = campaign.get("required_caption_text", "").strip()
    req_tag = campaign.get("required_channel_tag", "").strip()
    req_hashtags = campaign.get("required_hashtags", [])

    full_text = f"{clean_title} {caption}"
    append_blocks = []

    # Check required caption text
    if req_caption and req_caption.lower() not in full_text.lower():
        append_blocks.append(req_caption)
        modified = True

    # Check required channel tag
    if req_tag and req_tag.lower() not in full_text.lower():
        append_blocks.append(req_tag)
        modified = True

    # Check hashtags
    missing_hashtags = []
    for tag in req_hashtags:
        if tag.strip().lower() not in full_text.lower():
            missing_hashtags.append(tag.strip())

    if missing_hashtags:
        append_blocks.append(" ".join(missing_hashtags))
        modified = True

    compliant_caption = caption
    if append_blocks:
        compliant_caption += "\n\n" + "\n".join(append_blocks)

    # Enforce max 5 hashtags total: preserve required first, then extras up to 5
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
        compliant_caption = re.sub(r" +", " ", compliant_caption)
        modified = True

    return clean_title, compliant_caption.strip(), modified
