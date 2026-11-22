"""Pre-Flight System Health Check & Diagnostic Engine.

Performs a comprehensive, non-destructive read-only audit of the entire clipping workspace:
1. Verifies Python runtime (>= 3.10) and system binaries (FFmpeg, ffprobe, yt-dlp).
2. Verifies core Python package dependencies.
3. Asserts all workspace directories and configuration presets exist.
4. Validates .env configuration and tests Zernio API connection in read-only mode.
5. Verifies active campaign, editing rules, and fixed awake IST schedule.
6. Verifies memory, continuous learning templates, and auto-VOD watcher config.
7. Updates state/onboarding_state.json with health check results and setup_complete status.
"""

import datetime
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    ACCOUNTS_PATH,
    ASSETS_DIR,
    BASE_DIR,
    CAMPAIGN_PATH,
    CONFIG_DIR,
    EDITING_RULES_PATH,
    ENV_PATH,
    LEARNED_RULES_PATH,
    LOGS_DIR,
    MEMORY_DIR,
    OUTPUT_DIR,
    PERF_LOG_PATH,
    PRESETS_DIR,
    QUEUE_PATH,
    STATE_DIR,
    TEMP_DIR,
    VIRAL_DNA_PATH,
    WATCHED_STREAMERS_PATH,
    get_ytdlp_cmd,
    load_active_campaign,
    load_env,
    load_zernio_accounts,
)


def update_onboarding_health_status(all_passed: bool):
    """Updates state/onboarding_state.json with health check results."""
    onboarding_path = STATE_DIR / "onboarding_state.json"
    data = {}
    if onboarding_path.exists():
        try:
            with open(onboarding_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    if not data:
        template_path = STATE_DIR / "onboarding_state.template.json"
        if template_path.exists():
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

    if data:
        now_iso = datetime.datetime.now().astimezone().isoformat()
        steps = data.setdefault("steps", {})
        health_step = steps.setdefault("phase_c_health_check", {})
        health_step["status"] = "completed" if all_passed else "failed"
        health_step["completed_at"] = now_iso
        data["last_updated"] = now_iso

        if all_passed:
            data["setup_complete"] = True
            data["current_phase"] = "READY"
            data["current_step"] = "ready_to_clip"

        try:
            with open(onboarding_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass


def run_health_check(verbose: bool = True) -> bool:
    checks = []
    critical_failures = 0
    warnings = 0

    if verbose:
        print("=" * 80)
        print("🩺 SAIMGTA6CLIPPING — PRE-FLIGHT SYSTEM HEALTH CHECK (v3.0)")
        print("=" * 80)

    # 1. Python Environment Check
    py_v = sys.version_info
    py_str = f"v{py_v.major}.{py_v.minor}.{py_v.micro}"
    if py_v >= (3, 10):
        checks.append(("Python Runtime", True, f"{py_str} (>= 3.10 required)"))
    else:
        checks.append(("Python Runtime", False, f"{py_str} is unsupported; requires Python 3.10+"))
        critical_failures += 1

    # 2. System Binaries Check
    ffmpeg_p = shutil.which("ffmpeg")
    ffprobe_p = shutil.which("ffprobe")
    if ffmpeg_p and ffprobe_p:
        try:
            p = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            line = p.stdout.splitlines()[0].split("Copyright")[0].strip() if p.stdout else "detected"
            checks.append(("FFmpeg & ffprobe", True, line))
        except Exception:
            checks.append(("FFmpeg & ffprobe", True, "Binaries detected in system PATH"))
    else:
        missing_bin = []
        if not ffmpeg_p:
            missing_bin.append("ffmpeg")
        if not ffprobe_p:
            missing_bin.append("ffprobe")
        checks.append(("FFmpeg & ffprobe", False, f"Missing: {', '.join(missing_bin)}"))
        critical_failures += 1

    # 3. Core Python Dependencies
    required_pkgs = ["yt-dlp", "faster-whisper", "pillow", "numpy", "python-dotenv", "requests"]
    pkg_status = []
    all_pkgs_ok = True
    for pkg in required_pkgs:
        try:
            ver = importlib.metadata.version(pkg)
            pkg_status.append(f"{pkg} (v{ver})")
        except Exception:
            try:
                mod_name = "PIL" if pkg == "pillow" else ("dotenv" if pkg == "python-dotenv" else pkg.replace("-", "_"))
                __import__(mod_name)
                pkg_status.append(f"{pkg} (installed)")
            except Exception:
                all_pkgs_ok = False
                pkg_status.append(f"{pkg} (MISSING)")

    if all_pkgs_ok:
        checks.append(("Core Dependencies", True, "yt-dlp, faster-whisper, pillow, numpy, requests, dotenv"))
    else:
        checks.append(("Core Dependencies", False, ", ".join(pkg_status)))
        critical_failures += 1

    # 4. Workspace Directories
    dirs_to_check = [ASSETS_DIR, CONFIG_DIR, PRESETS_DIR, LOGS_DIR, MEMORY_DIR, OUTPUT_DIR, STATE_DIR, TEMP_DIR]
    missing_dirs = [d.name for d in dirs_to_check if not d.exists()]
    if not missing_dirs:
        checks.append(("Workspace Folders", True, f"{len(dirs_to_check)}/{len(dirs_to_check)} directories verified"))
    else:
        checks.append(("Workspace Folders", False, f"Missing directories: {', '.join(missing_dirs)}"))
        critical_failures += 1

    # 5. Active Campaign & Presets Check
    campaign_ok = False
    campaign_detail = "Missing config/active_campaign.json"
    if CAMPAIGN_PATH.exists():
        try:
            c = load_active_campaign()
            c_name = c.get("campaign_name", "Default")
            c_slug = c.get("campaign_slug", "custom")
            tags = " ".join(c.get("required_hashtags", []))
            campaign_detail = f"'{c_name}' (slug: {c_slug}) | {tags}"
            campaign_ok = True
        except Exception as e:
            campaign_detail = f"Error reading campaign: {e}"

    checks.append(("Active Campaign", campaign_ok, campaign_detail))
    if not campaign_ok:
        warnings += 1

    # Preset Library Check
    preset_files = list(PRESETS_DIR.glob("*.json")) if PRESETS_DIR.exists() else []
    if preset_files:
        checks.append(("Preset Library", True, f"{len(preset_files)} preset(s) in config/presets/"))
    else:
        checks.append(("Preset Library", False, "No presets found in config/presets/"))
        warnings += 1

    # 6. Schedule Configuration Check
    sched_ok = False
    sched_detail = "Missing config/schedule_config.json"
    sched_path = CONFIG_DIR / "schedule_config.json"
    if sched_path.exists():
        try:
            with open(sched_path, "r", encoding="utf-8") as f:
                s_cfg = json.load(f)
            slots = s_cfg.get("daily_slots_ist", [])
            cap = s_cfg.get("max_clips_per_day", 5)
            sched_detail = f"{cap} clips/day: {', '.join(slots)} IST -> UTC"
            sched_ok = True
        except Exception as e:
            sched_detail = f"Error reading schedule: {e}"

    checks.append(("Posting Schedule", sched_ok, sched_detail))
    if not sched_ok:
        warnings += 1

    # 7. Editing Rules Check
    rules_ok = False
    rules_detail = "Missing config/editing_rules.json"
    if EDITING_RULES_PATH.exists():
        try:
            with open(EDITING_RULES_PATH, "r", encoding="utf-8") as f:
                r_cfg = json.load(f)
            v = r_cfg.get("video", {})
            res = f"{v.get('width', 1080)}x{v.get('height', 1920)} @ {v.get('fps', 60)}fps"
            lufs = v.get("audio_loudnorm_lufs", -14)
            rules_detail = f"{res}, 35/65 split, {lufs} LUFS audio, 2.5s hook banner"
            rules_ok = True
        except Exception as e:
            rules_detail = f"Error reading editing_rules: {e}"

    checks.append(("Editing Rules", rules_ok, rules_detail))
    if not rules_ok:
        critical_failures += 1

    # 8. Credentials & Zernio API Connection Check
    env_vars = load_env()
    z_key = env_vars.get("ZERNIO_API_KEY") or os.environ.get("ZERNIO_API_KEY")
    if not z_key or z_key == "your_zernio_api_key_here":
        checks.append(("Zernio Credentials", False, "ZERNIO_API_KEY not configured in .env (Run python scripts/bootstrap.py --key <KEY>)"))
        warnings += 1
        zernio_conn_ok = False
        zernio_conn_detail = "Skipped (no API key)"
    else:
        checks.append(("Zernio Credentials", True, "ZERNIO_API_KEY present in .env"))
        # Test read-only API query
        try:
            from zernio_client import ZernioClient
            client = ZernioClient(api_key=z_key)
            resp = client._request("GET", "/accounts")
            accounts = resp.get("accounts", [])
            ig_acc = next((a for a in accounts if a.get("platform") == "instagram" and a.get("isActive")), None)
            yt_acc = next((a for a in accounts if a.get("platform") == "youtube" and a.get("isActive")), None)

            acc_details = []
            if ig_acc:
                acc_details.append(f"Instagram: @{ig_acc.get('username')}")
            if yt_acc:
                acc_details.append(f"YouTube: @{yt_acc.get('username')}")

            if ig_acc and yt_acc:
                zernio_conn_ok = True
                zernio_conn_detail = f"Connected ({', '.join(acc_details)})"
            elif ig_acc or yt_acc:
                zernio_conn_ok = True
                zernio_conn_detail = f"Partially Connected ({', '.join(acc_details)})"
            else:
                zernio_conn_ok = False
                zernio_conn_detail = "API active, but no connected accounts found at zernio.com"
                warnings += 1
        except Exception as e:
            zernio_conn_ok = False
            zernio_conn_detail = f"Connection failed: {str(e)[:80]}"
            warnings += 1

    checks.append(("Zernio Live API", zernio_conn_ok, zernio_conn_detail))

    # 9. Memory & Continuous Learning State Check
    memory_files = [
        ("learned_rules.md", LEARNED_RULES_PATH, MEMORY_DIR / "learned_rules.template.md"),
        ("viral_dna_weights.json", VIRAL_DNA_PATH, MEMORY_DIR / "viral_dna_weights.template.json"),
        ("performance_log.json", PERF_LOG_PATH, MEMORY_DIR / "performance_log.template.json"),
    ]
    mem_ok = True
    mem_details = []
    for name, target, tpl in memory_files:
        if target.exists() or tpl.exists():
            mem_details.append(name.split(".")[0])
        else:
            mem_ok = False
            mem_details.append(f"{name} (MISSING)")

    checks.append(("Continuous Learning", mem_ok, f"Templates verified ({', '.join(mem_details)})"))
    if not mem_ok:
        warnings += 1

    # 10. Auto-VOD Streamer Watcher Check
    streamer_ok = False
    streamer_detail = "Missing config/watched_streamers.json"
    if WATCHED_STREAMERS_PATH.exists():
        try:
            with open(WATCHED_STREAMERS_PATH, "r", encoding="utf-8") as f:
                s_data = json.load(f)
            s_list = s_data.get("streamers", [])
            streamer_detail = f"{len(s_list)} approved channels configured"
            streamer_ok = True
        except Exception as e:
            streamer_detail = f"Error reading watched_streamers: {e}"

    checks.append(("Auto-VOD Watcher", streamer_ok, streamer_detail))
    if not streamer_ok:
        warnings += 1

    # Print summary table
    if verbose:
        for name, ok, detail in checks:
            mark = "✔" if ok else ("⚠" if warnings else "✖")
            status_color = f"[{mark}]"
            print(f"{status_color:<5} {name:<24}: {detail}")

        print("-" * 80)
        overall_healthy = (critical_failures == 0)
        if overall_healthy and warnings == 0:
            print("🎉 STATUS: 100% HEALTHY — READY FOR AUTONOMOUS CLIPPING & AUTO-POSTING!")
        elif overall_healthy:
            print(f"✅ STATUS: FUNCTIONAL WITH {warnings} SETUP NOTICES (Ready for clipping; complete remaining setup steps)")
        else:
            print(f"❌ STATUS: {critical_failures} CRITICAL FAILURE(S) DETECTED (Resolve items marked [✖] before running)")
        print("=" * 80)

    all_passed = (critical_failures == 0)
    update_onboarding_health_status(all_passed)
    return all_passed


if __name__ == "__main__":
    run_health_check(verbose=True)
