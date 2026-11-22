# SaimGTA6Clipping (v3.0)

> **Plug-and-Play, Autonomous GTA 6 Stream Clipping & Auto-Posting Studio.**  
> Built for creators, agencies, and clipping studios with an anti-hallucination chunked state machine, smart priority onboarding wizard, campaign preset switcher, auto-VOD watcher, closed-loop analytics learning engine, and Whop Content Rewards compliance.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-6.0%2B-green.svg)](https://ffmpeg.org/)
[![BYOK](https://img.shields.io/badge/Setup-BYOK%20Ready-success.svg)](https://zernio.com)

---

## ⚡ What Makes v3.0 Special?

1. **Priority-Ordered Resumable Onboarding Wizard (`SKILL.md`):**
   - Walks new users through setup **one step at a time** in strict priority order, tracking progress in `state/onboarding_state.json`.
   - **Smart Agent-vs-Manual Boundary:** The agent automatically runs scripts, configures templates, discovers API account IDs, and converts timezones. The user only completes strictly manual actions (account sign-ups, OAuth approvals, Whop campaign joins).
2. **Saved Campaign Preset Library (`config/presets/` + `"switch campaign"`):**
   - Automatically saves every Whop campaign brief as a reusable preset in `config/presets/<campaign_slug>.json`.
   - Switch active campaigns instantly in chat (`"switch campaign"`) or CLI (`python main.py --switch-campaign <SLUG_OR_#>`) with zero manual JSON editing.
3. **Auto-VOD Streamer Watcher (`scripts/vod_watcher.py` + `"check new streams"`):**
   - Scans approved streamer channels (`config/watched_streamers.json`) for fresh VODs using lightweight `yt-dlp --flat-playlist --dump-json` (metadata only — **NEVER** downloads full videos).
   - Ranks fresh streams by view velocity, publish recency, and learned streamer weights. Reply `"clip #1"` to begin atomic clipping immediately.
4. **Deterministic Auto-Ranker (`scripts/moment_selector.py`):**
   - Calculates numeric `predicted_viral_score` (0–100) combining base score, moment archetype, hook formula, duration bucket, streamer source, and YouTube Heatmap spike bonus.
   - Auto-sorts pending candidates in `state/job_queue.json` highest-score-first, reserving an 80% proven / 20% exploratory A/B test split.
5. **Self-Optimizing Viral Learning Engine (`scripts/viral_learner.py`):**
   - Closed-loop feedback pulling live views, likes, comments, shares, watch time, and Reels skip rates via Zernio Analytics API v1.
   - Settled 24h / 48h / 72h snapshot logic + 6h early warnings, 3,000-view payout alert, and `--clone-winners` blueprint generator.
   - Auto-rewrites compact `memory/learned_rules.md` (strictly ≤ 40 lines).
6. **2026 Universal Safe-Zone Layout (1080×1920 @ 60fps):**
   - Universal safe box (`890×1250 px`, `x = 60..940`, `y = 250..1490`). Zero text or faces covered by Reels/Shorts UI buttons.
   - Centered 4–7 word opening hook banner at `y = 290px` (or `y = 360px` with logo).
   - Word-by-word `#FFE600` yellow active-word pop ASS captions at `y = 1150–1320px`.
   - `-14 LUFS` loudnorm audio normalization with silence trimming (>0.6s).
   - Dynamic campaign watermark preserving exact 3:1 aspect ratio with zero banner overlap.
7. **Pre-Flight System Health Check (`scripts/health_check.py`):**
   - Comprehensive diagnostic engine auditing binaries, dependencies, configs, presets, memory, and live Zernio connections in read-only mode.

---

## 🛠️ 1-Step Installation & Quick Start (BYOK)

### 1. Clone & Lean Bootstrap
```bash
git clone https://github.com/sammd2899-commits/saimgta6clipping.git
cd saimgta6clipping

# Auto-verify tools, scaffold workspace, and unpack templates:
python scripts/bootstrap.py
```

### 2. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your credentials:
```env
# Zernio API Key (from https://zernio.com — 2 free social slots)
ZERNIO_API_KEY=your_zernio_api_key_here
POST_INTERVAL_HOURS=2.0

# Optional: Telegram bot notifications for published clips
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Verify System Health
```bash
python main.py --health-check
```

---

## 💬 Natural Language Chat Commands

When using SaimGTA6Clipping inside an AI agent (such as Antigravity), use these natural chat commands:

| Chat Command | What It Does |
|---|---|
| **`"check new streams"`** | Scans watched streamer channels and lists fresh unclipped VODs ranked by viral score. |
| **Paste YouTube URL** *(or `"clip #1"`)* | Plans, auto-ranks candidates, and starts atomic 1-clip execution. |
| **`"switch campaign"`** | Shows your saved campaign preset library and switches active campaign instantly. |
| **`"update campaign"`** | Parses a new Whop brief, saves active campaign + reusable preset in `config/presets/`. |
| **`"update schedule"`** | Modifies daily posting slots or daily cap in `config/schedule_config.json`. |
| **`"fetch live URLs"`** | Checks Zernio for published posts and displays clean Whop submission links. |
| **`"mark submitted"`** | Flags newly live links as submitted so they don't reappear in future lists. |
| **`"learn from analytics"`** | Pulls 24h/48h/72h Zernio metrics, upgrades Viral DNA weights, and rewrites learned rules. |
| **`"clone winners"`** | Outputs top 3 winning clips and a Viral DNA clone blueprint for the next batch. |
| **`"health check"`** | Runs non-destructive pre-flight diagnostic check across all tools, configs, and APIs. |

---

## 💻 Terminal CLI Command Reference

| Command | Description |
|---|---|
| `python main.py <URL>` | Full automated clipping & scheduling pipeline on a video/stream |
| `python main.py --check-streams` | Check watched streamer channels for fresh unclipped VODs |
| `python main.py --list-streamers` | List approved streamer channels in `config/watched_streamers.json` |
| `python main.py --list-presets` | View all saved campaign presets in `config/presets/` |
| `python main.py --switch-campaign <SLUG_OR_#>` | Switch active campaign to a preset |
| `python main.py --health-check` | Run non-destructive system health diagnostics |
| `python main.py --resume` | Resume pending clips from `state/job_queue.json` |
| `python main.py --show-queue` | View current job queue status & viral scores |
| `python main.py --show-campaign` | View active campaign compliance rules |
| `python main.py --show-schedule` | View calculated awake-hour posting slots |
| `python main.py --fetch-urls` | Fetch live URLs of published clips for Whop |
| `python main.py --mark-submitted` | Mark live clips as submitted in log |
| `python main.py --learn-analytics` | Run closed-loop Viral Learning Engine |
| `python main.py --clone-winners` | Print top winning clips and clone blueprint |
| `python scripts/test_dry_run.py` | Run 12-clip dry-run simulation suite |
| `python scripts/test_candidate_ranking.py` | Run unit tests for moment scoring & auto-ranker |

---

## 📁 Repository Structure

```
D:\saimgta6clipping\
├── .env.example                       # Clean BYOK credential template (Zernio & Telegram)
├── .gitignore                         # Strict isolation for secrets, local state, media & memory
├── main.py                            # Master CLI entry point with preset switcher & VOD watcher
├── requirements.txt                   # Minimal, lean clipping dependencies (zero bloat)
├── SKILL.md                           # Priority-ordered resumable onboarding wizard & agent spec
├── GUIDE.md                           # Post-setup operational & system understanding guide
├── README.md                          # Full architectural documentation & setup guide
├── assets\                            # Campaign logos & watermarks (.gitkeep)
├── config\
│   ├── active_campaign.example.json   # Template for active campaign brief
│   ├── editing_rules.json             # Global visual layout, safe zones, and audio rules
│   ├── schedule_config.example.json   # Fixed awake IST schedule & Tier-1 peak slot examples
│   ├── watched_streamers.example.json # Approved streamer channels to watch
│   ├── zernio_accounts.example.json   # Template for connected YouTube & Instagram accounts
│   └── presets\
│       └── example_campaign.json      # Starter campaign preset template
├── core\
│   ├── adapter.py                     # Compatibility bridge for external clipping CLIs
│   └── __init__.py
├── memory\
│   ├── learned_rules.template.md      # Concise continuous learning template (≤ 40 lines)
│   ├── performance_log.template.json  # Analytics snapshot schema template
│   └── viral_dna_weights.template.json# Cold-start 1.0x baseline weights template
├── state\
│   └── onboarding_state.template.json # State schema for resumable onboarding wizard
└── scripts\
    ├── analyzer.py                    # Stage 1: Heatmap discovery & state-machine planner
    ├── bootstrap.py                   # Lean 1-command auto-installer & environment initializer
    ├── campaign_manager.py            # Campaign preset switcher & brief parser
    ├── config_manager.py              # Dynamic cross-platform path resolver & compliance gate
    ├── downloader.py                  # Targeted segment downloader (yt-dlp --download-sections)
    ├── editor.py                      # Vertical clip editor & ffprobe verification interface
    ├── fetch_live_urls.py             # Whop Submission Helper & live URL tracker
    ├── health_check.py                # Pre-flight diagnostic check & onboarding state updater
    ├── metadata_generator.py          # High-CTR copy generator using viral DNA weights
    ├── moment_selector.py             # Deterministic candidate auto-ranker & score_candidate()
    ├── pipeline.py                    # Stage 2: Atomic 1-clip loop with resume support
    ├── scheduler.py                   # Fixed awake IST scheduler engine (IST -> UTC)
    ├── telegram_live_notifier.py      # Both-Live Telegram alert daemon with 5-minute failsafe
    ├── telegram_notifier.py           # Telegram bot notifier with auto chat ID detection
    ├── test_candidate_ranking.py      # Unit test suite for deterministic moment scoring
    ├── test_dry_run.py                # 12-clip dry-run verification suite
    ├── viral_enhancer.py              # Master 1080x1920 60fps renderer, hook banner & ASS captions
    ├── viral_learner.py               # Closed-loop Viral Learning Engine & winner cloner
    ├── vod_watcher.py                 # Auto-VOD streamer watcher & fresh stream ranker
    └── zernio_client.py               # Standard-library urllib Zernio API v1 client
```

---

## ⚖️ Attribution & Acknowledgements

* **Original Concept & Inspiration:** SaimGTA6Clipping incorporates workflows and concepts inspired by [beyondtahir/beyondgtaclips](https://github.com/beyondtahir/beyondgtaclips) for stream moment detection.
* **Open Source Tools:** Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [FFmpeg](https://ffmpeg.org/), and [Pillow](https://python-pillow.org/).

---

## 📄 License

MIT License.
