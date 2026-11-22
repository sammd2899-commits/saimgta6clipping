---
name: saimgta6clipping
description: Automated GTA 6 viral clipping studio with deterministic auto-ranking, closed-loop analytics learning engine, 2026 safe-zone visual enhancer (1080x1920 60fps, 2.5s hook banner, word-pop ASS captions), fixed awake IST scheduling (Asia/Kolkata -> UTC), and Whop Content Rewards compliance. Use when asked to clip GTA 6 streams, generate viral Shorts/Reels, manage campaign rules, schedule clips, learn from analytics, or clone winners.
---

# SaimGTA6Clipping

Autonomous GTA 6 Stream Clipping & Scheduled Auto-Posting Pipeline.  
Engineered for zero-hallucination, chunked execution on high-speed and lightweight models (such as Gemini Flash).

---

## 0. First Run / Zero-Manual-Setup Onboarding

When triggered on a new machine or empty environment:

1. **Auto-Bootstrap:**
   Run the bootstrapper to verify dependencies, scaffold directories, and unpack templates:
   ```bash
   python scripts/bootstrap.py
   ```
2. **Collect User Configuration:**
   Prompt the user in chat for the following 3 quick inputs:
   - **Zernio API Key:** Save to `.env` (`ZERNIO_API_KEY=...`) and run `python main.py --verify-zernio` to sync connected Instagram and YouTube accounts.
   - **Active Campaign Brief:** Save to `config/active_campaign.json` (Campaign name, required caption attribution, creator tag, required hashtags, and optional watermark path).
   - **Posting Schedule:** Confirm timezone and awake-hour slots in `config/schedule_config.json` (default 5 clips/day: 14:00, 16:00, 18:00, 20:00, 22:00 IST).
3. **Notify User:**
   Output: *"Setup complete — paste your first GTA 6 YouTube livestream link to start clipping!"*

---

## 1. Natural Language Chat Commands

The assistant recognizes and executes the following chat triggers:

| User Chat Intent | Action Executed | Behind-the-Scenes Command |
|---|---|---|
| **Paste YouTube URL** | Runs Stage 1 Plan & Queue, auto-ranks candidates, then executes the atomic 1-clip loop | `python main.py <URL>` |
| `"update campaign"` | Prompts for new brief text, extracts rules, and locks them into `config/active_campaign.json` | `python scripts/campaign_manager.py` |
| `"update schedule"` | Prompts for new IST awake slots or daily posting cap and updates `config/schedule_config.json` | `python main.py --show-schedule` |
| `"fetch live URLs"` | Checks Zernio for published posts, updates `logs/published_clips.json`, and displays clean Whop submission links | `python main.py --fetch-urls` |
| `"mark submitted"` | Marks newly live clips as `whop_submitted: true` so they never clutter future Whop submission lists | `python main.py --mark-submitted` |
| `"learn from analytics"` | Runs closed-loop Viral Learning Engine across live Zernio metrics, updates Viral DNA weights & learned rules | `python main.py --learn-analytics` |
| `"clone winners"` | Analyzes top performing clips and prints actionable Viral DNA clone blueprint for the next batch | `python main.py --clone-winners` |
| `"resume queue"` | Resumes pending clips from interrupted runs | `python main.py --resume` |

---

## 2. Anti-Hallucination Architecture (1-Clip-at-a-Time Loop)

Lightweight models (like Gemini Flash) risk context drift or hallucination if tasked with batch-processing multi-hour streams simultaneously. SaimGTA6Clipping enforces strict architectural isolation:

1. **Stage 1 (Plan & Queue Only):**
   - Fetches video metadata and YouTube Most Replayed heatmap without downloading the multi-hour VOD.
   - Calculates deterministic `predicted_viral_score` (0–100) using base score, archetype weights, duration bucket, streamer source, and heatmap spike bonus.
   - Sorts candidates highest-score-first in `state/job_queue.json`, reserving an 80% proven / 20% A/B test split.
   - Assigns collision-free awake IST slots (Asia/Kolkata mapped to ISO 8601 UTC).

2. **Stage 2 (Atomic 1-by-1 Stop-and-Approve Execution):**
   - **Download:** Downloads ONLY that 1 clip's timestamp window (~25s) into `temp/` via `yt-dlp --download-sections`. Disk usage never exceeds 150 MB.
   - **Visual Enhancement:** Renders 1080×1920 60fps vertical MP4:
     * 35/65 stacked facecam/gameplay split or blurred background fill (zero black bars).
     * 2.5s opening hook banner in universal safe zone (`y = 290px` or `y = 360px` with logo).
     * Word-by-word `#FFE600` yellow pop ASS captions (`y = 1150–1320px`).
     * -14 LUFS loudnorm audio normalization with silence trimming.
     * Dynamic campaign watermark overlay preserving exact 3:1 aspect ratio for 100% duration with zero banner overlap.
   - **Hard ffprobe Gate:** Asserts 1080×1920, valid audio & video streams, duration within 12–55s.
   - **Compliance Gate:** Enforces title ≤ 65 chars (+ `#Shorts`), max 5 hashtags, and mandatory campaign tags.
   - **Schedule & Cleanup:** Uploads to Zernio API v1 via direct presigned URL, records `post_id`, purges temporary segment from disk, and advances to the next clip.

---

## 3. Fixed Awake-Hour Schedule (Asia/Kolkata -> UTC)

Guarantees **zero overnight posts** and hits peak Tier-1 Western discovery windows:
- **Daily Slots:** `14:00`, `16:00`, `18:00`, `20:00`, `22:00` IST (2:00 PM, 4:00 PM, 6:00 PM, 8:00 PM, 10:00 PM)
- **UTC Conversion for Zernio:**
  - `14:00 IST` → `08:30:00Z` (UK/EU morning wake-up)
  - `16:00 IST` → `10:30:00Z` (US East Coast wake-up)
  - `18:00 IST` → `12:30:00Z` (US East Coast morning commute)
  - `20:00 IST` → `14:30:00Z` (US East Coast mid-morning peak)
  - `22:00 IST` → `16:30:00Z` (US lunch & West Coast wake-up)
- **Automatic Rollover:** Once 5 slots for the day are filled, automatically assigns slots starting tomorrow at 14:00 IST.

---

## 4. Self-Optimizing Viral Learning Engine

Run periodically or on command (`python main.py --learn-analytics`):
- Pulls live views, likes, comments, shares, average watch time, and Reels skip rates from Zernio Analytics API.
- Settled 24h / 48h / 72h snapshot tracking + 6h early warning flags.
- Quantifies Viral DNA into `memory/viral_dna_weights.json` (archetypes, duration sweet spots, hook formulas, IST slots, streamer source weights).
- Rewrites concise `memory/learned_rules.md` strictly capped at ≤ 40 lines.
- Alerts on 3,000-view payout milestones and warns on zero-view anomalies.

---

## 5. Optional Global Skill Integrations

SaimGTA6Clipping is fully modular and integrates cleanly with companion skills if installed:
- **`earshot` (Offline SFX / Foley):** If available, can add subtle gameplay riser whooshes or impact stingers to opening hooks during the `viral_enhancer` pipeline.
- **`continuous-learning-v2`:** If present in the parent environment, hooks into runtime observation events to log persistent cross-session heuristics into `.gemini/` or local memory.
