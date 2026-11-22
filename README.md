# SaimGTA6Clipping (v2.0)

> **Autonomous GTA 6 Stream Clipping, Auto-Ranking & Scheduled Multi-Platform Studio.**  
> Engineered with an anti-hallucination chunked state machine, 2026 universal safe-zone video enhancement (1080×1920 60fps), closed-loop analytics learning engine, fixed awake IST scheduling, and Whop Content Rewards compliance.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-6.0%2B-green.svg)](https://ffmpeg.org/)

---

## 🚀 Key Features in v2.0

1. **Self-Optimizing Viral Learning Engine (`scripts/viral_learner.py`):**
   - Closed-loop analytics feedback pulling live views, likes, comments, shares, watch time, and Reels skip rates via Zernio Analytics API v1.
   - Settled 24h / 48h / 72h snapshot logic + 6h early warning flags.
   - Quantifies Viral DNA into `memory/viral_dna_weights.json` (archetype performance, duration sweet spots, hook formulas, IST slot velocity, streamer source weights).
   - Auto-rewrites compact `memory/learned_rules.md` (capped strictly at ≤ 40 lines) without overriding mandatory compliance.
   - 80/20 A/B Testing: allocates 80% of queue to proven viral winners and 20% to exploratory tweaks.
   - Automated 3,000-view payout alerts and zero-view / copyright mute warnings.
   - Winner Clone Blueprint: instant "Part 2" finder (`--clone-winners`).

2. **Deterministic Auto-Ranker (`scripts/moment_selector.py`):**
   - Deterministic `score_candidate()` formula computing `predicted_viral_score` (0–100) combining base score, archetype weight, hook formula weight, duration sweet spot, streamer source weight, and YouTube Heatmap peak bonus.
   - Auto-sorts pending candidates in `state/job_queue.json` highest-score-first before processing.

3. **Both-Live Telegram Notifier & Whop Helper (`scripts/telegram_live_notifier.py`, `scripts/fetch_live_urls.py`):**
   - Smart zero-cost Telegram notifier polls until **BOTH YouTube Short and Instagram Reel** are publicly live, with a 5-minute failsafe and a 30-minute Whop submission countdown alert.
   - Whop Live-URL Helper displays clean copy-paste submission blocks and tracks `whop_submitted: true` to prevent duplicates.

4. **2026 Universal Safe-Zone Layout (1080×1920 @ 60fps):**
   - **Universal Safe Box:** `890×1250 px` (`x = 60..940`, `y = 250..1490`). Zero text, faces, or HUD covered by Reels/Shorts UI buttons.
   - **Opening Hook Banner:** 4–7 bold words at `y = 290px` (or `y = 360px` with logo), active only from `0.0s – 2.5s`.
   - **Split Screen:** 35% facecam top (reaction centered) / 65% gameplay bottom with blurred vertical fill fallback (NO black bars).
   - **Dynamic Word Captions:** 68px ASS captions at `y = 1150–1320px` with `#FFE600` yellow active-word pop and 5px black outline.
   - **Audio Standards:** -14 LUFS loudnorm (`loudnorm=I=-14:TP=-1.5:LRA=11`) with silence trimming (>0.6s).
   - **Dynamic Watermark Overlay:** Preserves exact 3:1 aspect ratio for 100% of clip duration with zero overlap against opening hook banner.
   - **Hard ffprobe Gate:** Asserts 1080×1920, audio/video streams, and duration bounds before scheduling.

5. **Fixed Awake-Hour Schedule (Asia/Kolkata -> UTC):**
   - Automatically maps 5 clips/day to `14:00`, `16:00`, `18:00`, `20:00`, `22:00` IST.
   - Converts to ISO 8601 UTC for Zernio `scheduledFor` to hit US & European peak morning/evening discovery windows.
   - Guarantees **zero overnight posts** with clean rollover to the next day.

---

## 📁 Repository Structure

```
D:\saimgta6clipping\
├── .env.example                       # Clean BYOK credential template (Zernio & Telegram)
├── .gitignore                         # Strict isolation for secrets, local state, media & memory
├── main.py                            # Master CLI entry point
├── requirements.txt                   # Minimal Python package dependencies
├── SKILL.md                           # Antigravity & Agent skill specification
├── README.md                          # Full architectural documentation & setup guide
├── assets\                            # Directory for campaign logos / watermarks (.gitkeep)
├── config\
│   ├── active_campaign.example.json   # Template for Whop campaign brief & attribution rules
│   ├── editing_rules.json             # Global visual layout, safe zones, and audio rules
│   ├── schedule_config.example.json   # Fixed awake IST schedule & Tier-1 peak slot examples
│   └── zernio_accounts.example.json   # Template for connected YouTube & Instagram accounts
├── core\
│   ├── adapter.py                     # Compatibility bridge for external clipping CLIs
│   └── __init__.py
├── memory\
│   ├── learned_rules.template.md      # Concise continuous learning template (≤ 40 lines)
│   ├── performance_log.template.json  # Analytics snapshot schema template
│   └── viral_dna_weights.template.json# Cold-start 1.0x baseline weights template
└── scripts\
    ├── analyzer.py                    # Stage 1: Heatmap discovery & state-machine planner
    ├── bootstrap.py                   # Automated zero-manual-setup environment initializer
    ├── campaign_manager.py            # Campaign brief parser & rule manager
    ├── config_manager.py              # Dynamic cross-platform path resolver & compliance gate
    ├── downloader.py                  # Targeted segment downloader (yt-dlp --download-sections)
    ├── editor.py                      # Vertical clip editor & ffprobe verification interface
    ├── fetch_live_urls.py             # Whop Submission Helper & live URL tracker
    ├── metadata_generator.py          # High-CTR copy generator using viral DNA weights
    ├── moment_selector.py             # Deterministic candidate auto-ranker & score_candidate()
    ├── pipeline.py                    # Stage 2: Atomic one-by-one execution loop with resume support
    ├── scheduler.py                   # Fixed awake IST scheduler engine (IST -> UTC)
    ├── telegram_live_notifier.py      # Both-Live Telegram alert daemon with 5-minute failsafe
    ├── telegram_notifier.py           # Telegram bot notifier with auto chat ID detection
    ├── test_candidate_ranking.py      # Unit test suite for deterministic moment scoring
    ├── test_dry_run.py                # 12-clip dry-run verification suite
    ├── viral_enhancer.py              # Master 1080x1920 60fps renderer, hook banner & ASS captions
    ├── viral_learner.py               # Closed-loop Viral Learning Engine & winner cloner
    └── zernio_client.py               # Standard-library urllib Zernio API v1 client
```

---

## 🛠️ BYOK Quick Start (Bring Your Own Keys)

### 1. Clone & Bootstrap
```bash
git clone https://github.com/sammd2899-commits/saimgta6clipping.git
cd saimgta6clipping

# Initialize folders, unpack templates, and verify dependencies:
python scripts/bootstrap.py
```

### 2. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your Zernio API key:
```env
ZERNIO_API_KEY=your_zernio_api_key_here
POST_INTERVAL_HOURS=2.0

# Optional: Telegram bot for instant mobile links
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

Verify your Zernio connection and cache your connected accounts:
```bash
python main.py --verify-zernio
```

### 3. Set Up Your Active Campaign
Customize `config/active_campaign.json` or paste your brief directly into chat:
```bash
python main.py --show-campaign
```

### 4. Clip Your First Stream
```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

## 💬 Natural Language Chat Commands

When used inside an AI coding assistant (such as Antigravity), simply speak naturally:

- **"Clip this stream: `<URL>`"** → Discovers moments, auto-ranks them, and runs atomic 1-clip cycles.
- **"Update campaign"** → Prompts for new campaign requirements and locks them in.
- **"Update schedule"** → Modifies posting slots or daily clip limits.
- **"Fetch live URLs"** → Pulls live Instagram & YouTube URLs ready for Whop submission.
- **"Mark submitted"** → Flags live links as submitted so they don't reappear.
- **"Learn from analytics"** → Queries Zernio Analytics and updates Viral DNA weights.
- **"Clone winners"** → Outputs a detailed breakdown of top performers and a blueprint for the next batch.

---

## 💻 Terminal CLI Command Reference

| Command | Description |
|---|---|
| `python main.py <URL>` | Full automated clipping & scheduling pipeline |
| `python main.py <URL> --plan-only` | Run Stage 1 (discover moments & populate queue) |
| `python main.py --resume` | Resume pending clips in `state/job_queue.json` |
| `python main.py --show-queue` | View current job queue status & viral scores |
| `python main.py --show-campaign` | View active Whop campaign compliance rules |
| `python main.py --show-schedule` | View calculated awake-hour posting slots |
| `python main.py --fetch-urls` | Fetch live URLs of published clips for Whop |
| `python main.py --mark-submitted` | Mark live clips as submitted in log |
| `python main.py --learn-analytics` | Run closed-loop Viral Learning Engine |
| `python main.py --clone-winners` | Print top 3 winning clips and clone blueprint |
| `python main.py --learn "<RULE>"` | Append directive to continuous learning memory |
| `python scripts/test_dry_run.py` | Run 12-clip dry-run scheduling & compliance tests |
| `python scripts/test_candidate_ranking.py` | Run unit tests for moment scoring & auto-ranker |

---

## ⚖️ Attribution & Acknowledgements

* **Original Concept & Inspiration:** SaimGTA6Clipping incorporates workflows and concepts inspired by [beyondtahir/beyondgtaclips](https://github.com/beyondtahir/beyondgtaclips) for stream moment detection.
* **Open Source Tools:** Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [FFmpeg](https://ffmpeg.org/), and [Pillow](https://python-pillow.org/).

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
