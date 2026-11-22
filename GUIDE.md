# SaimGTA6Clipping — Complete System & Operational Guide

Welcome to **SaimGTA6Clipping (v3.0)**! This guide explains how your autonomous clipping engine operates, how to execute daily clipping routines in under 5 minutes, and how the self-learning brain compounds views over time.

---

## 1. How the Whole System Works (Simple Visual Flow)

```
[ Step 1: Discover Fresh Stream ]
   │
   ├─► Chat: "check new streams"  ──► vod_watcher.py scans approved channels
   │                                   (metadata only via yt-dlp flat-playlist)
   │
   └─► User pastes YouTube URL (or replies "clip #1")
           │
           ▼
[ Step 2: Stage 1 — Discover & Auto-Rank Moments ]
   │
   ├─► YouTube Most Replayed Heatmap discovery (avoids downloading multi-hour VOD)
   ├─► score_candidate() formula (0–100) calculates predicted_viral_score:
   │   Base + Archetype + Hook Formula + Duration Bucket + Streamer Weight + Spike Bonus
   ├─► Auto-sorts highest-score-first into state/job_queue.json
   └─► Reserves 80% proven viral DNA / 20% exploratory A/B test slots
           │
           ▼
[ Step 3: Stage 2 — Atomic 1-Clip-at-a-Time Loop ]
   │
   ├─► Downloads ONLY that 1 clip's ~25s window into temp/ (disk usage < 150 MB)
   ├─► Renders 1080×1920 60fps vertical format:
   │   • 35% facecam / 65% gameplay split (or blurred-fill fallback with NO black bars)
   │   • 2.5s opening hook banner in universal safe zone (y = 290px or 360px with logo)
   │   • Word-by-word #FFE600 active-word yellow pop ASS captions (y = 1150–1320px)
   │   • -14 LUFS loudnorm audio normalization with silence trimming (>0.6s)
   │   • Campaign watermark logo overlay (preserves exact 3:1 aspect ratio)
   ├─► Hard Python ffprobe verification (resolution, audio streams, 12s–55s duration)
   ├─► Compliance Gate: auto-appends required tags/credits, enforces title ≤ 65 chars & max 5 hashtags
   ├─► Direct presigned binary upload & scheduling to Zernio API v1 (fixed awake IST slot)
   ├─► Purges raw temp file from disk immediately
   └─► Stops & asks user for approval before the next clip (anti-hallucination design)
           │
           ▼
[ Step 4: Publish & Submission ]
   │
   ├─► Zernio publishes post to Instagram Reel & YouTube Short at exact same second
   ├─► Telegram Both-Live Notifier (or "fetch live URLs") alerts you when BOTH are live
   └─► You copy the direct URLs and paste into Whop Content Rewards within 30 minutes
           │
           ▼
[ Step 5: Self-Learning Feedback Loop ]
   │
   └─► "learn from analytics" (viral_learner.py)
       • Pulls settled 24h, 48h, and 72h views, retention, skip-rate & streamer velocity
       • Updates memory/viral_dna_weights.json with new mathematical weights
       • Rewrites memory/learned_rules.md (compact, strictly ≤ 40 lines)
       • Auto-promotes winning A/B tests and refines future candidate ranking!
```

---

## 2. Why the 1-Clip-at-a-Time Loop Matters (Anti-Hallucination)

Lightweight models (like Gemini Flash) excel at fast, deterministic reasoning but can hallucinate timestamps or drop compliance tags when forced to process multi-hour livestreams in massive, unchunked batches.

SaimGTA6Clipping enforces strict architectural boundaries:
- **Zero Full-VOD Downloads:** Only small ~25s windows are downloaded.
- **Atomic State Transitions:** Clip state transitions from `PENDING` → `SCHEDULED` → logged to `logs/published_clips.json` one by one.
- **Hard Code Gates:** Python checks the video file directly with `ffprobe` and enforces campaign tags before any upload call is made.

---

## 3. Built-In Chat Commands Cheat Sheet

You can control the entire studio directly from your AI chat:

| Chat Command | What It Does |
|---|---|
| **`"check new streams"`** | Scans watched streamer channels and lists fresh unclipped VODs ranked by viral potential. |
| **Paste YouTube URL** *(or reply `"clip #1"`)* | Plans, auto-ranks, and processes clips one by one. |
| **`"switch campaign"`** | Shows your saved campaign preset library and switches active campaign instantly. |
| **`"update campaign"`** | Parses a new Whop brief, saves it to `config/active_campaign.json` AND as a reusable preset. |
| **`"fetch live URLs"`** | Checks Zernio for newly live posts and displays clean copy-paste links for Whop. |
| **`"mark submitted"`** | Flags live links as submitted so they don't clutter future Whop submission lists. |
| **`"learn from analytics"`** | Queries Zernio Analytics for settled metrics and updates Viral DNA weights. |
| **`"clone winners"`** | Prints top 3 winning clips and a step-by-step blueprint for your next batch. |
| **`"update schedule"`** | Customizes daily awake-hour slots and daily clip posting limits. |
| **`"setup optional tools"`** | Configure Telegram bot notifications, Cloudflare R2, or optional MCPs. |

---

## 4. Daily 5-Minute Routine for Maximum Earnings

Following this exact 5-minute routine ensures consistent algorithmic growth and protects your social accounts:

1. **Morning (1 Minute) — Check Streams:**
   - Type `"check new streams"`.
   - Review the top recommended fresh stream and reply `"clip #1"`.
   - The agent extracts and schedules your clips across your awake IST slots (`14:00`, `16:00`, `18:00`, `20:00`, `22:00` IST).
2. **Throughout the Day (1 Minute per Slot) — Whop Submission:**
   - When your phone pings via Telegram (or when you type `"fetch live URLs"` 5 minutes after a scheduled slot):
   - Copy the live Instagram Reel link and YouTube Short link.
   - Go to your Whop campaign dashboard and submit the links within 30 minutes of going live.
   - Reply `"mark submitted"` to keep your unsubmitted list clean.
3. **Evening / Weekly (1 Minute) — Viral Brain Optimization:**
   - Type `"learn from analytics"` to ingest performance metrics from clips published 24h–72h ago.
   - Type `"clone winners"` to see which archetypes, hook styles, and streamers generated the highest view velocity.

---

## 5. Account Safety & Payout Rules

To protect your accounts from algorithmic shadowbans and ensure you qualify for Whop Content Rewards payouts:

- **Warm-Up Rule (First 3 Days):** Post strictly **3–5 clips per day** during the first 3–5 days of a new Instagram / YouTube channel. Never spam 10+ clips on day one.
- **Strict No-Bot Whop Boundary:** Never automate logins or submissions to Whop or Meta directly. Always perform Whop link submissions manually in your browser to avoid anti-bot disqualifications.
- **Tier-1 Geography Signal:** Keep your YouTube channel country set to **United States** and your Instagram location tag set to **Miami, Florida**. Tier-1 views (US, UK, Canada, Australia) pay the highest rewards.
- **60-Day Post Retention:** Never delete or archive published clips for at least 60 days. Whop crawlers verify that posts remain live and publicly viewable to approve payouts.
- **Comments & Likes Visible:** Always keep comments enabled and likes publicly visible. Engagement rate calculations require public comment counts.
