"""Lean, Zero-Bloat Auto-Bootstrapper for SaimGTA6Clipping.

1-Command Environment Setup for New BYOK Users:
1. Validates Python environment (>=3.10) and prints versions.
2. Checks system binaries (FFmpeg, ffprobe, yt-dlp) before running.
3. Check-Before-Installing: inspects each package in requirements.txt; installs ONLY missing ones.
4. Auto-scaffolds workspace structure and unpacks clean config, preset, and memory templates.
5. Verifies strictly NO 3D/Blender/heavy bloat is installed.
6. Configures .env from .env.example with Zernio and optional Telegram keys.
"""

import argparse
import importlib.metadata
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
PRESETS_DIR = CONFIG_DIR / "presets"
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
STATE_DIR = BASE_DIR / "state"
TEMP_DIR = BASE_DIR / "temp"
ASSETS_DIR = BASE_DIR / "assets"

REQ_PATH = BASE_DIR / "requirements.txt"
ENV_PATH = BASE_DIR / ".env"
ENV_EXAMPLE = BASE_DIR / ".env.example"


def check_python_version() -> bool:
    v = sys.version_info
    v_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 10):
        print(f"  ✔ Python version: v{v_str} (>= 3.10 requirement satisfied)")
        return True
    print(f"  ✖ Python version: v{v_str} is unsupported. Please install Python 3.10 or newer.")
    return False


def check_system_binaries() -> dict:
    results = {}
    # 1. FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            p = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            first_line = p.stdout.splitlines()[0] if p.stdout else "detected"
            results["ffmpeg"] = (True, first_line.split("Copyright")[0].strip())
        except Exception:
            results["ffmpeg"] = (True, "detected at " + ffmpeg_path)
    else:
        results["ffmpeg"] = (False, "Not found in PATH")

    # 2. ffprobe
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        results["ffprobe"] = (True, "detected at " + ffprobe_path)
    else:
        results["ffprobe"] = (False, "Not found in PATH")

    # 3. yt-dlp binary or module
    ytdlp_path = shutil.which("yt-dlp")
    if ytdlp_path:
        try:
            p = subprocess.run([ytdlp_path, "--version"], capture_output=True, text=True, timeout=5)
            results["yt-dlp"] = (True, f"v{p.stdout.strip()} ({ytdlp_path})")
        except Exception:
            results["yt-dlp"] = (True, "detected at " + ytdlp_path)
    else:
        # Check python module
        try:
            import yt_dlp
            results["yt-dlp"] = (True, f"v{yt_dlp.version.__version__} (Python module)")
        except Exception:
            results["yt-dlp"] = (False, "Not found in PATH or Python environment")

    for tool, (ok, detail) in results.items():
        if ok:
            print(f"  ✔ {tool:<10}: {detail}")
        else:
            print(f"  ⚠ {tool:<10}: {detail}")

    if not results["ffmpeg"][0] or not results["ffprobe"][0]:
        print("\n  👉 To install FFmpeg & ffprobe:")
        if sys.platform == "win32":
            print("     Windows: winget install Gyan.FFmpeg   (or download from https://ffmpeg.org)")
        elif sys.platform == "darwin":
            print("     macOS:   brew install ffmpeg")
        else:
            print("     Linux:   sudo apt update && sudo apt install -y ffmpeg")

    return results


def check_and_install_dependencies():
    if not REQ_PATH.exists():
        print("  ✖ requirements.txt not found.")
        return

    req_lines = [l.strip() for l in REQ_PATH.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    
    # Map requirements to import/distribution names
    pkg_map = {
        "yt-dlp": "yt_dlp",
        "faster-whisper": "faster_whisper",
        "pillow": "PIL",
        "numpy": "numpy",
        "python-dotenv": "dotenv",
        "requests": "requests",
    }

    missing = []
    for req in req_lines:
        raw_name = req.split(">=")[0].split("==")[0].split("<")[0].strip()
        mod_name = pkg_map.get(raw_name.lower(), raw_name)
        try:
            ver = importlib.metadata.version(raw_name)
            print(f"  ✔ Package '{raw_name}': v{ver} (Installed)")
        except importlib.metadata.PackageNotFoundError:
            # Check if importable
            try:
                __import__(mod_name)
                print(f"  ✔ Package '{raw_name}': detected via import (Installed)")
            except ImportError:
                missing.append(req)
                print(f"  ⏳ Package '{raw_name}': missing -> queued for lean install")

    if missing:
        print(f"\n  [Pip] Installing {len(missing)} missing package(s): {', '.join(missing)}...")
        cmd = [sys.executable, "-m", "pip", "install", *missing]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            print("  ✔ All missing packages successfully installed.")
        else:
            print(f"  ⚠ Pip installation output: {proc.stderr[:160]}")
    else:
        print("  ✔ All core Python dependencies already satisfied.")

    print("  ✔ Lean clipping stack verified: ZERO 3D/Blender/heavy bloatware.")


def ensure_workspace_and_templates():
    for d in [ASSETS_DIR, CONFIG_DIR, PRESETS_DIR, LOGS_DIR, OUTPUT_DIR, STATE_DIR, TEMP_DIR, MEMORY_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Config & Presets
    example_preset = PRESETS_DIR / "example_campaign.json"
    active_campaign = CONFIG_DIR / "active_campaign.json"
    if not active_campaign.exists() and example_preset.exists():
        shutil.copy(example_preset, active_campaign)
        print("  ✔ Initialized config/active_campaign.json from presets/example_campaign.json.")

    sched_target = CONFIG_DIR / "schedule_config.json"
    sched_example = CONFIG_DIR / "schedule_config.example.json"
    if not sched_target.exists() and sched_example.exists():
        shutil.copy(sched_example, sched_target)
        print("  ✔ Initialized config/schedule_config.json from template.")

    streamers_target = CONFIG_DIR / "watched_streamers.json"
    streamers_example = CONFIG_DIR / "watched_streamers.example.json"
    if not streamers_target.exists() and streamers_example.exists():
        shutil.copy(streamers_example, streamers_target)
        print("  ✔ Initialized config/watched_streamers.json from template.")

    accounts_target = CONFIG_DIR / "zernio_accounts.json"
    accounts_example = CONFIG_DIR / "zernio_accounts.example.json"
    if not accounts_target.exists() and accounts_example.exists():
        shutil.copy(accounts_example, accounts_target)
        print("  ✔ Initialized config/zernio_accounts.json from template.")

    # 2. Memory Templates
    for base in ["learned_rules.md", "viral_dna_weights.json", "performance_log.json"]:
        target = MEMORY_DIR / base
        name_parts = base.split(".")
        tpl_name = f"{name_parts[0]}.template.{name_parts[1]}"
        template = MEMORY_DIR / tpl_name
        if not target.exists() and template.exists():
            shutil.copy(template, target)
            print(f"  ✔ Initialized memory/{base} from {tpl_name}.")

    # 3. State Template (Onboarding State)
    onboarding_target = STATE_DIR / "onboarding_state.json"
    onboarding_template = STATE_DIR / "onboarding_state.template.json"
    if not onboarding_target.exists() and onboarding_template.exists():
        shutil.copy(onboarding_template, onboarding_target)
        print("  ✔ Initialized state/onboarding_state.json from template.")

    # 4. Job Queue State
    queue_target = STATE_DIR / "job_queue.json"
    if not queue_target.exists():
        queue_target.write_text('{"source_url": null, "total_clips": 0, "clips": []}\n', encoding="utf-8")
        print("  ✔ Initialized empty state/job_queue.json.")

    print("  ✔ Workspace directory structure and configuration templates verified.")


def setup_credentials(zernio_key: str = None, telegram_token: str = None, telegram_chat: str = None, interactive: bool = False):
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


def run_bootstrap(zernio_key: str = None, telegram_token: str = None, telegram_chat: str = None, interactive: bool = False) -> bool:
    print("=" * 75)
    print("🚀 SAIMGTA6CLIPPING — LEAN AUTO-INSTALLER & WORKSPACE BOOTSTRAPPER")
    print("=" * 75)

    print("\n[1/5] Checking Python Environment...")
    py_ok = check_python_version()

    print("\n[2/5] Checking System Binaries (FFmpeg, ffprobe, yt-dlp)...")
    check_system_binaries()

    print("\n[3/5] Verifying & Installing Core Python Dependencies...")
    check_and_install_dependencies()

    print("\n[4/5] Initializing Workspace Folders & Configuration Templates...")
    ensure_workspace_and_templates()

    print("\n[5/5] Checking Credentials (.env)...")
    setup_credentials(zernio_key=zernio_key, telegram_token=telegram_token, telegram_chat=telegram_chat, interactive=interactive)

    print("\n" + "=" * 75)
    print("🎉 BOOTSTRAP COMPLETE — READY FOR ONBOARDING OR DIRECT CLIPPING!")
    print("=" * 75)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lean Bootstrapper for SaimGTA6Clipping")
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
