---
name: saimgta6clipping
description: Automated GTA 6 viral clipping studio with anti-hallucination chunked state machine, 2026 safe-zone visual enhancer (1080x1920, 60fps, 2.5s hook banner, word-pop ASS captions), Zernio multi-platform scheduling, and Whop Content Rewards compliance. Use when asked to clip GTA 6 livestreams, generate viral Shorts/Reels, manage campaign rules, or schedule clips.
---

# SaimGTA6Clipping

Autonomous GTA 6 Stream Clipping & Scheduled Auto-Posting Pipeline.
Engineered for zero-hallucination, chunked execution on high-speed and lightweight models.

## 0. First Run / Zero-Manual-Setup Onboarding

When triggered on a new machine or empty environment:

1. **Auto-Bootstrap:**
   Run the bootstrapper to verify dependencies and scaffold directories:
   ```bash
   python scripts/bootstrap.py
   ```
2. **Collect User Configuration:**
   Prompt the user in chat for the following 3 quick inputs:
   - **Zernio API Key:** Save to `.env` (`ZERNIO_API_KEY=...`) and run `python main.py --verify-zernio` to sync connected Instagram and YouTube accounts.
   - **Active Campaign Brief:** Save to `config/active_campaign.json` (Campaign name, required caption attribution, creator tag, and required hashtags).
   - **Posting Schedule:** Confirm timezone and awake-hour slots in `config/schedule_config.json` (default 5 clips/day: 14:00, 16:00, 18:00, 20:00, 22:00 IST).
3. **Notify User:**
   Output: *"Setup complete — paste your first GTA 6 YouTube livestream link to start clipping!"*

---

## 1. Core Workflow & Trigger Commands

### A. Clip & Schedule Livestream
When the user pastes a YouTube livestream or VOD URL:
```bash
python main.py <YOUTUBE_URL>
```
* **Stage 1 (Plan & Queue):** Downloads metadata and Most Replayed heatmap, picks 18–38s viral moments opening directly on action, maps awake-hour posting slots, and stores candidates in `state/job_queue.json`.
* **Stage 2 (Atomic Loop):** For each clip:
  1. Downloads only that 25s window via `yt-dlp --download-sections`.
  2. Renders 1080×1920 60fps clip with 2.5s opening hook banner (`y=290px`) and dynamic word-by-word ASS captions (`y=1150–1320px`).
  3. Verifies via `ffprobe` (1080×1920, valid audio/video, duration 12–55s).
  4. Generates compliant YouTube title (≤65 chars + `#Shorts`) and Instagram caption (≤5 hashtags + DM-share trigger).
  5. Schedules via Zernio API v1 (`scheduledFor`).
  6. Purges temporary segment from disk.

### B. Resume Interrupted Jobs
```bash
python main.py --resume
```

### C. Whop Submission Helper
Fetch live published URLs to submit to Whop Content Rewards:
```bash
python main.py --fetch-urls
```
Mark submitted clips:
```bash
python main.py --mark-submitted
```

### D. Campaign & Continuous Learning
- View active campaign: `python main.py --show-campaign`
- View job queue: `python main.py --show-queue`
- View learned rules: `python main.py --show-rules`
- Add learned preference: `python main.py --learn "<DIRECTIVE>"`
