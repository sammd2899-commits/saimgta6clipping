# SaimGTA6Clipping

> Autonomous GTA 6 Stream Clipping & Multi-Platform Auto-Posting Studio.  
> Combines anti-hallucination chunked state execution, 2026 universal safe-zone video enhancement, dynamic word-pop captions, and automated Zernio scheduling.

---

## Architecture & Features

1. **Anti-Hallucination Chunked Pipeline (`state/job_queue.json`):**
   - Two-stage architecture: Stage 1 discovers moments from YouTube metadata and Most Replayed heatmap; Stage 2 processes one clip at a time.
   - Targeted downloading via `yt-dlp --download-sections` avoids downloading multi-hour VODs.
   - Automatic temp segment cleanup keeps disk usage under 150 MB.
   - Built-in resume support recovers interrupted runs instantly.

2. **2026 Universal Safe-Zone Layout (1080×1920, 9:16):**
   - **Universal Safe Box:** 890×1250 px (`x = 60..940`, `y = 250..1490`). Zero text or faces covered by Reels/Shorts UI buttons.
   - **Opening Hook Banner:** Centered at `y = 290 px`, 4–7 bold words, active only from `0.0s – 2.5s`.
   - **Layout Options:** Stacked 35% facecam / 65% gameplay split-screen, or full-bleed vertical fill with blurred background (NO black bars).
   - **Dynamic Word Captions:** 68px ASS captions positioned strictly at `y = 1150–1320 px` with `#FFE600` yellow active-word pop and 5px black outline.
   - **Audio Standards:** Audio normalized to **-14 LUFS** (`loudnorm=I=-14:TP=-1.5:LRA=11`) with silence trimming (>0.6s).
   - **Quality:** 1080×1920 @ 60.0 fps, H.264, 6 Mbps.

3. **Viral Moment Selector:**
   - Filters candidate moments: prioritizes creepy/smart NPC AI, police chases, ragdoll crash physics, easter eggs, and instant karma fails.
   - Strictly skips story cutscenes, loud licensed radio songs, and NSFW scenes.
   - Targets 18–38 seconds per clip, opening immediately on chaos/reaction.

4. **Multi-Platform Auto-Posting (Zernio API v1):**
   - Schedules Instagram Reels and YouTube Shorts across configurable awake hours.
   - Enforces Instagram's 5-hashtag cap and includes DM-share triggers.
   - Enforces YouTube's ≤65-character curiosity-gap titles with `#Shorts`.
   - Tracks live published post URLs via `scripts/fetch_live_urls.py` for manual Whop submission.

5. **Continuous Learning Loop:**
   - `memory/learned_rules.md` persists user directives, editing preferences, and compliance rules across runs.

---

## Quick Start (Plug-and-Play)

### 1. Installation
Clone the repository:
```bash
git clone https://github.com/sammd2899-commits/saimgta6clipping.git
cd saimgta6clipping
```

Run the automated bootstrapper:
```bash
python scripts/bootstrap.py
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and add your Zernio API key:
```bash
cp .env.example .env
```
Sync connected Instagram and YouTube accounts:
```bash
python main.py --verify-zernio
```

### 3. Clip Your First Stream
```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

## CLI Command Reference

| Command | Description |
|---|---|
| `python main.py <URL>` | Full automated clipping & scheduling pipeline |
| `python main.py <URL> --plan-only` | Run Stage 1 (discover moments & populate queue) |
| `python main.py --resume` | Resume pending clips in `state/job_queue.json` |
| `python main.py --show-queue` | View current job queue status |
| `python main.py --show-campaign` | View active Whop campaign compliance rules |
| `python main.py --show-schedule` | View calculated awake-hour posting slots |
| `python main.py --fetch-urls` | Fetch live URLs of published clips for Whop |
| `python main.py --mark-submitted` | Mark clips as submitted in log |
| `python main.py --learn "<RULE>"` | Append directive to continuous learning memory |

---

## Attribution & Acknowledgements

* **Original Concept & Inspiration:** SaimGTA6Clipping incorporates workflows inspired by [beyondtahir/beyondgtaclips](https://github.com/beyondtahir/beyondgtaclips) for stream moment detection.
* **Open Source Tools:** Built with [yt-dlp](https://github.com/yt-dlp/yt-dlp), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [FFmpeg](https://ffmpeg.org/), and [Pillow](https://python-pillow.org/).

---

## License

MIT License. See [LICENSE](LICENSE) for details.
