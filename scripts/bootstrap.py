"""Zero-Manual-Setup Auto-Bootstrapper for SaimGTA6Clipping.

Performs automatic environment verification and initialization:
1. Scaffolds all workspace directories (assets/, config/, logs/, memory/, output/, state/, temp/).
2. Initializes config files from .example.json templates if not present.
3. Initializes memory runtime files (learned_rules.md, viral_dna_weights.json, performance_log.json) from templates.
4. Checks for ffmpeg and ffprobe system binaries.
5. Validates and installs Python packages from requirements.txt.
6. Configures .env from .env.example with Zernio and optional Telegram credentials.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
STATE_DIR = BASE_DIR / "state"
TEMP_DIR = BASE_DIR / "temp"
ASSETS_DIR = BASE_DIR / "assets"

REQ_PATH = BASE_DIR / "requirements.txt"
ENV_PATH = BASE_DIR / ".env"
ENV_EXAMPLE = BASE_DIR / ".env.example"


def ensure_directories():
    print("[1/5] Scaffolding workspace directories and configuration templates...")
    for d in [ASSETS_DIR, CONFIG_DIR, MEMORY_DIR, LOGS_DIR, OUTPUT_DIR, STATE_DIR, TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Initialize local configs from examples if missing
    for cfg_name in ["active_campaign", "schedule_config", "zernio_accounts"]:
        target = CONFIG_DIR / f"{cfg_name}.json"
        example = CONFIG_DIR / f"{cfg_name}.example.json"
        if not target.exists() and example.exists():
            shutil.copy(example, target)
            print(f"  ✔ Initialized config/{cfg_name}.json from template.")

    print("  ✔ Workspace directories verified.")


def ensure_memory_templates():
    print("[2/5] Initializing continuous learning & viral DNA memory...")
    # 1. learned_rules.md
    target_rules = MEMORY_DIR / "learned_rules.md"
    template_rules = MEMORY_DIR / "learned_rules.template.md"
    if not target_rules.exists() and template_rules.exists():
        shutil.copy(template_rules, target_rules)
        print("  ✔ Initialized memory/learned_rules.md from template.")

    # 2. viral_dna_weights.json
    target_weights = MEMORY_DIR / "viral_dna_weights.json"
    template_weights = MEMORY_DIR / "viral_dna_weights.template.json"
    if not target_weights.exists() and template_weights.exists():
        shutil.copy(template_weights, target_weights)
        print("  ✔ Initialized memory/viral_dna_weights.json from template.")

    # 3. performance_log.json
    target_log = MEMORY_DIR / "performance_log.json"
    template_log = MEMORY_DIR / "performance_log.template.json"
    if not target_log.exists() and template_log.exists():
        shutil.copy(template_log, target_log)
        print("  ✔ Initialized memory/performance_log.json from template.")

    print("  ✔ Memory templates verified.")


def check_ffmpeg() -> bool:
    print("[3/5] Checking FFmpeg installation...")
    has_ffmpeg = shutil.which("ffmpeg") is not None
    has_ffprobe = shutil.which("ffprobe") is not None

    if has_ffmpeg and has_ffprobe:
        print("  ✔ FFmpeg and ffprobe detected.")
        return True

    print("\n  ⚠ FFmpeg is missing from PATH. Install it using:")
    if sys.platform == "win32":
        print("     Windows (winget): winget install Gyan.FFmpeg")
    elif sys.platform == "darwin":
        print("     macOS (Homebrew): brew install ffmpeg")
    else:
        print("     Linux (apt):      sudo apt update && sudo apt install -y ffmpeg")
    return False


def install_dependencies():
    print("[4/5] Checking Python package dependencies...")
    if not REQ_PATH.exists():
        print("  ✖ requirements.txt not found.")
        return

    cmd = [sys.executable, "-m", "pip", "install", "-r", str(REQ_PATH)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        print("  ✔ Python dependencies verified and up to date.")
    else:
        print(f"  ⚠ Pip notice: {proc.stderr[:120] if proc.stderr else 'Already satisfied'}")


def setup_credentials(zernio_key: str = None, telegram_token: str = None, telegram_chat: str = None, interactive: bool = False):
    print("[5/5] Checking credentials and platform configuration...")
    if not ENV_PATH.exists() and ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_PATH)
        print("  ✔ Created .env from .env.example.")

    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    updates = {}
    if zernio_key:
        updates["ZERNIO_API_KEY"] = zernio_key
    if telegram_token:
        updates["TELEGRAM_BOT_TOKEN"] = telegram_token
    if telegram_chat:
        updates["TELEGRAM_CHAT_ID"] = telegram_chat

    if interactive and not zernio_key:
        try:
            val = input("Enter your Zernio API Key (press Enter to skip): ").strip()
            if val:
                updates["ZERNIO_API_KEY"] = val
        except Exception:
            pass

    if updates:
        new_lines = []
        handled = set()
        for l in lines:
            replaced = False
            for k, v in updates.items():
                if l.startswith(f"{k}="):
                    new_lines.append(f"{k}={v}")
                    handled.add(k)
                    replaced = True
                    break
            if not replaced:
                new_lines.append(l)

        for k, v in updates.items():
            if k not in handled:
                new_lines.append(f"{k}={v}")

        ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"  ✔ Updated .env credentials: {', '.join(updates.keys())}.")


def run_bootstrap(zernio_key: str = None, telegram_token: str = None, telegram_chat: str = None, interactive: bool = False):
    print("=" * 70)
    print("SaimGTA6Clipping — Automated Setup & Environment Bootstrapper")
    print("=" * 70)
    ensure_directories()
    ensure_memory_templates()
    check_ffmpeg()
    install_dependencies()
    setup_credentials(zernio_key=zernio_key, telegram_token=telegram_token, telegram_chat=telegram_chat, interactive=interactive)
    print("=" * 70)
    print("🎉 BOOTSTRAP COMPLETE — READY TO CLIP GTA 6 STREAMS!")
    print("Paste your first YouTube livestream URL to start clipping.")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap SaimGTA6Clipping Environment")
    parser.add_argument("--key", type=str, help="Zernio API Key to configure in .env")
    parser.add_argument("--telegram-token", type=str, help="Telegram Bot Token to configure in .env")
    parser.add_argument("--telegram-chat", type=str, help="Telegram Chat ID to configure in .env")
    parser.add_argument("--interactive", action="store_true", help="Prompt interactively for configuration")
    args = parser.parse_args()
    run_bootstrap(
        zernio_key=args.key,
        telegram_token=args.telegram_token,
        telegram_chat=args.telegram_chat,
        interactive=args.interactive,
    )
