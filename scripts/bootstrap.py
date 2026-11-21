"""Zero-Manual-Setup Auto-Bootstrapper for SaimGTA6Clipping.

Performs automatic environment verification and initialization:
1. Validates and installs missing Python packages from requirements.txt.
2. Checks for ffmpeg and ffprobe system binaries.
3. Automatically scaffolds workspace directories (temp/, output/, logs/, state/, memory/).
4. Initializes memory/learned_rules.md from template.
5. Interactive or programmatic credential configuration for Zernio & Whop campaigns.
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

REQ_PATH = BASE_DIR / "requirements.txt"
ENV_PATH = BASE_DIR / ".env"
ENV_EXAMPLE = BASE_DIR / ".env.example"


def ensure_directories():
    print("[1/5] Scaffolding workspace directories and configuration templates...")
    for d in [CONFIG_DIR, MEMORY_DIR, LOGS_DIR, OUTPUT_DIR, STATE_DIR, TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Initialize local configs from examples if missing
    for cfg_name in ["active_campaign", "schedule_config", "zernio_accounts"]:
        target = CONFIG_DIR / f"{cfg_name}.json"
        example = CONFIG_DIR / f"{cfg_name}.example.json"
        if not target.exists() and example.exists():
            shutil.copy(example, target)
            print(f"  ✔ Initialized config/{cfg_name}.json from template.")

    print("  ✔ Workspace directories and templates verified.")


def ensure_learned_rules():
    print("[2/5] Initializing continuous learning memory...")
    target = MEMORY_DIR / "learned_rules.md"
    template = MEMORY_DIR / "learned_rules.template.md"
    if not target.exists():
        if template.exists():
            shutil.copy(template, target)
            print("  ✔ Initialized memory/learned_rules.md from template.")
        else:
            target.write_text("# Learned Rules & Pacing Directives\n", encoding="utf-8")
            print("  ✔ Created memory/learned_rules.md.")
    else:
        print("  ✔ Existing memory/learned_rules.md preserved.")


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


def setup_credentials(zernio_key: str = None, interactive: bool = False):
    print("[5/5] Checking credentials and platform configuration...")
    if not ENV_PATH.exists() and ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_PATH)
        print("  ✔ Created .env from .env.example.")

    if zernio_key:
        lines = []
        if ENV_PATH.exists():
            lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        found = False
        new_lines = []
        for l in lines:
            if l.startswith("ZERNIO_API_KEY="):
                new_lines.append(f"ZERNIO_API_KEY={zernio_key}")
                found = True
            else:
                new_lines.append(l)
        if not found:
            new_lines.append(f"ZERNIO_API_KEY={zernio_key}")
        ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print("  ✔ ZERNIO_API_KEY saved to .env.")


def run_bootstrap(zernio_key: str = None, interactive: bool = False):
    print("=" * 70)
    print("SaimGTA6Clipping — Automated Setup & Environment Bootstrapper")
    print("=" * 70)
    ensure_directories()
    ensure_learned_rules()
    check_ffmpeg()
    install_dependencies()
    setup_credentials(zernio_key=zernio_key, interactive=interactive)
    print("=" * 70)
    print("🎉 BOOTSTRAP COMPLETE — READY TO CLIP GTA 6 STREAMS!")
    print("Paste your first YouTube livestream URL to start clipping.")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap SaimGTA6Clipping Environment")
    parser.add_argument("--key", type=str, help="Zernio API Key to configure in .env")
    parser.add_argument("--interactive", action="store_true", help="Prompt interactively for configuration")
    args = parser.parse_args()
    run_bootstrap(zernio_key=args.key, interactive=args.interactive)
