---
name: saimgta6clipping
description: Automated GTA 6 stream clipping studio with priority-ordered resumable onboarding wizard, auto-VOD streamer watcher, campaign preset switcher, deterministic candidate auto-ranking, 2026 safe-zone visual enhancer (1080x1920 60fps, 2.5s hook banner, word-pop ASS captions), Zernio multi-platform scheduling, and Whop Content Rewards compliance. Use when asked to clip GTA 6 livestreams, set up the clipping workspace, check new streams, switch campaign presets, learn from analytics, or clone winners.
---

# SaimGTA6Clipping

Autonomous GTA 6 Stream Clipping, Auto-Ranking & Scheduled Multi-Platform Studio (v4.0 Dual-Mode).  
Supports both Mode 1 (Local Web App at `http://127.0.0.1:8765` via `start_web.bat`) and Mode 2 (AI Agent Skill / Chat).
Engineered with an anti-hallucination chunked state machine, smart agent-vs-manual automation, and persistent continuous learning.

---

## 0. Resumable Onboarding Architecture

Whenever the user activates this skill or says *"set up clipping"*, *"start setup"*, or runs on a fresh workspace:

1. **Inspect Onboarding State:**
   Read `state/onboarding_state.json` (or initialize it from `state/onboarding_state.template.json` via `python scripts/bootstrap.py`).
2. **Resume at Exact Pending Step:**
   Check `setup_complete`. If `true`, output:
   *"Workspace is 100% verified and ready! Say 'check new streams' to scan watched channels, or paste any YouTube livestream link to start clipping."*
   If `false`, resume execution at the first step where `status == "pending"`.
3. **Core Automation Rule for the Agent:**
   > Anything the agent can do itself (running scripts, creating configs, generating brand assets, discovering API account IDs, parsing campaign briefs into presets, converting timezones to UTC, writing `.env`, running health checks), the agent **MUST do automatically**.
   > Only hand over strictly required human actions (account sign-ups, OAuth logins, 2FA, and Whop clicks) as ultra-short numbered checklists—and wait for user confirmation before advancing.

---

## 1. Phase A — Required Core Setup (Execute in Strict Order)

### Step 1: Auto-Install Tools & Workspace (`Agent Automated`)
- **Agent Action:** Run `python scripts/bootstrap.py`.
- **Behavior:** The script checks whether Python >= 3.10, FFmpeg/ffprobe, yt-dlp, and core packages are installed, installs missing packages without 3D/Blender bloatware, and scaffolds folders and templates.
- **Agent Output:** Report green status checks, update `steps.step_1_bootstrap.status = "completed"`, and immediately proceed to Step 2.

### Step 2: Brand & Channel Kit Generation (`Agent Automated`)
- **Agent Action:** Ask the user **ONLY 1 question**:
  *"What is your target niche/game (default: GTA 6 / Gaming) and preferred brand vibe (e.g. Neon Miami Vice, Dark Street Heists, High-Energy Glitch Reactions)?"*
- **Agent Automation:** Upon receiving the reply (or if user accepts defaults), automatically generate and write `config/brand_kit.md`:
  - Matching **Instagram + YouTube channel name** (e.g., `ViceCityClips_`, `GTA6Pursuits`, `HeistPulse`)
  - Unique handle ideas (`@vicecityclips_`, `@gta6pursuits`)
  - Optimized bio & description with discovery keywords and Tier-1 engagement hooks
  - 15 YouTube channel search keywords (e.g., `GTA 6, GTA VI, GTA 6 clips, Vice City gameplay...`)
  - Profile picture, banner, and logo prompt specifications
- **State Update:** Mark `steps.step_2_brand_kit.status = "completed"`.

### Step 3: Instagram & Meta Professional Setup (`Hybrid: Agent Prepares, User Links`)
- **Agent Automation:**
  Hard-lock Instagram rules in `config/editing_rules.json`: `max_hashtags: 5`, `default_ig_location: "Miami, Florida"`, DM-share trigger at line 1, and 1080×1920 60fps universal safe zones.
- **User Checklist:** Hand the user ONLY the manual actions:
  1. Open Instagram on mobile or browser → Settings → **Switch to Professional Account (Creator)**.
  2. Ensure account is **Public** and **Likes/View Count Visible** is ON.
  3. Open `facebook.com` on your existing personal FB account → Create/open a Facebook Page → Page Settings → **Linked Accounts → Connect Instagram** (critical for Zernio Reel scheduling).
  4. Paste the channel name, handle, and bio from `config/brand_kit.md`.
- **Wait Condition:** Wait for user to reply *"Instagram linked"* or *"Done"*, then mark `steps.step_3_instagram_meta.status = "completed"`.

### Step 4: YouTube Channel Setup (`Hybrid: Agent Prepares, User Toggles`)
- **Agent Automation:**
  Hard-lock YouTube compliance in upload pipeline: `made_for_kids: false`, `comments_enabled: true`, `privacy: "public"`, and `≤65 char curiosity title + #Shorts`.
- **User Checklist:** Hand the user ONLY the manual actions in YouTube Studio (`studio.youtube.com`):
  1. Apply channel name, handle, and bio from `config/brand_kit.md`.
  2. In **Settings → Channel → Basic Info**: Set Country of Residence to **United States** (essential for Tier-1 algorithmic discovery and payouts). Paste channel keywords.
  3. In **Settings → Channel → Feature Eligibility**: Verify phone number to unlock custom thumbnails and 10+ daily Shorts uploads.
  4. In **Settings → Upload Defaults → Advanced**: Set Category to **Gaming**, Language to **English**, and Comments to **Allow all**.
- **Wait Condition:** Wait for user to reply *"YouTube ready"* or *"Done"*, then mark `steps.step_4_youtube_channel.status = "completed"`.

### Step 5: Zernio Multi-Platform API Connection (`Agent Auto-Discovers Everything`)
- **User Action:**
  Ask the user ONLY to sign up at `zernio.com` (free tier: 2 social accounts), connect their Instagram and YouTube channels via OAuth, and paste their `ZERNIO_API_KEY`.
- **Agent Automation:**
  1. Write `ZERNIO_API_KEY` to `.env`.
  2. Run `client.discover_and_save_accounts()` or `python main.py --verify-zernio`.
  3. Auto-discover both `accountId`s, verify active status, and write `config/zernio_accounts.json`.
  4. Confirm connection: *"Successfully connected Instagram (@...) and YouTube (@...) via Zernio!"*
- **State Update:** Mark `steps.step_5_zernio_connection.status = "completed"`.

### Step 6: Whop Campaign Preset, Watched Streamers & Schedule (`Strict No-Bot Boundary`)
- **Strict Anti-Bot Rule:** **NEVER automate, scrape, or log into Whop directly** (protects user from anti-bot bans).
- **User Action:** Give the user a 3-line guide:
  1. Sign into `contentrewards.com/c/discover` and connect your Instagram & YouTube in Settings.
  2. Join your desired GTA 6 campaign.
  3. Paste the **campaign brief text** into chat, drop any required campaign logo PNG into `assets/`, provide optional favorite streamer channels to watch, and state your timezone & awake hours (default: Asia/Kolkata, 14:00–22:00 IST).
- **Agent Automation:**
  1. Parse the brief into `config/active_campaign.json` AND save as a reusable preset in `config/presets/<slug>.json` via `campaign_manager.save_campaign_preset()`.
  2. Populate `config/watched_streamers.json` with approved channel URLs.
  3. Generate `config/schedule_config.json` with 5 awake-hour slots mapped cleanly to ISO 8601 UTC.
- **State Update:** Mark `steps.step_6_campaign_and_schedule.status = "completed"`.

---

## 2. Phase B — Optional Enhancements (Menu — User Can Enable or Skip)

After Phase A completes, present this clean menu:
*"Phase A Core Setup is complete! Would you like to configure any of these optional upgrades now, or type 'skip' to jump straight to pre-flight health check?"*

1. **Both-Live Telegram Mobile Notifier (Recommended):**
   - If user says yes: prompt for `TELEGRAM_BOT_TOKEN` (via `@BotFather`) and `TELEGRAM_CHAT_ID` (via `@userinfobot`), write to `.env`, test ping with `python scripts/telegram_notifier.py --test`, and set `optional_telegram.status = "completed"`.
2. **Cloudflare Media Hosting & Webhooks (Advanced Optional):**
   - For users needing Cloudflare R2 public URLs or Worker webhook relays. If skipped, mark `optional_cloudflare.status = "skipped"`.
3. **Optional Companion Skills (Suggested Only):**
   - Suggest `earshot` (CPU-only offline sound design/whooshes) and `continuous-learning-v2` (cross-session instinct learning). Never force-install.

---

## 3. Phase C — Pre-Flight Health Check (`scripts/health_check.py`)

- **Agent Action:** Run `python scripts/health_check.py`.
- **Verification:** Audits binaries, dependencies, folders, presets, schedule, editing rules, and Zernio connection.
- **Completion:** Sets `setup_complete: true` in `state/onboarding_state.json`.
- **Guide Delivery Rule:** **Present `GUIDE.md` ONLY NOW** after Phase C passes. Never dump the operational guide before setup is finished.
- **Final Prompt:**
  *"🎉 Setup complete and verified 100%! Run 'check new streams' to discover fresh VODs, or paste a YouTube livestream link to start clipping."*

---

## 4. Operational Chat Commands Reference

| User Chat Intent | Action Executed | Behind-the-Scenes Command |
|---|---|---|
| **`"check new streams"`** | Scans watched channels with `vod_watcher.py` and ranks fresh unclipped streams | `python main.py --check-streams` |
| **Paste YouTube URL** *(or `"clip #1"`)* | Plans, auto-ranks candidates, and starts atomic 1-clip execution | `python main.py <URL_OR_#>` |
| **`"update campaign"`** | Parses new Whop brief, saves active campaign + reusable preset in `config/presets/` | `python scripts/campaign_manager.py` |
| **`"switch campaign"`** | Lists saved presets and switches active campaign instantly | `python main.py --switch-campaign` |
| **`"update schedule"`** | Modifies daily posting slots or daily cap in `config/schedule_config.json` | `python main.py --show-schedule` |
| **`"fetch live URLs"`** | Checks Zernio for published posts and displays clean Whop submission links | `python main.py --fetch-urls` |
| **`"mark submitted"`** | Flags newly live links as submitted so they don't reappear in future lists | `python main.py --mark-submitted` |
| **`"learn from analytics"`** | Pulls 24h/48h/72h Zernio metrics, upgrades Viral DNA weights, and rewrites learned rules | `python main.py --learn-analytics` |
| **`"clone winners"`** | Outputs top 3 winning clips and a Viral DNA clone blueprint for the next batch | `python main.py --clone-winners` |
| **`"health check"`** | Runs non-destructive diagnostic check on all tools, configs, and APIs | `python main.py --health-check` |
| **`"setup optional tools"`** | Reruns Phase B menu to configure Telegram, Cloudflare, or extra skills | Custom prompt |

---

## 6. Multi-Reference Campaign Analyzer & BYOK Gemini AI (v4.2)

### 6.1 Bring-Your-Own-Key (BYOK) Gemini AI Backend
- SaimClip Studio supports Google Gemini (`gemini-2.5-flash`) for local AI moment selection, reference material analysis, and profile generation.
- Users can obtain a free key at `aistudio.google.com` and save it via **Setup → Step 5** or `.env` (`GEMINI_API_KEY=`).
- **Deterministic Zero-Dependency Fallback:** If `GEMINI_API_KEY` is not configured, the entire pipeline automatically falls back to deterministic heuristic algorithms and high-converting templates with zero crashes.

### 6.2 Multi-Reference Campaign Style Extraction
- In **Presets → New Campaign Preset**, users can add multiple reference inputs (`+ Add Reference`):
  - Reference Video URLs (YouTube, Drive, Instagram)
  - Style, pacing, and visual formatting notes
- `scripts/reference_analyzer.py` inspects all references and generates a persistent `reference_style_profile` containing:
  - `pacing`: Pacing target (e.g. "Fast-paced 20-24s sweet spot with chaos opening in first 0.8s")
  - `hook_style`: Specific hook banner wording and safe zone position
  - `caption_tone`: Word pop highlights and subtitle energy
  - `layout`: Layout mode (`split-35-65` vs `blurred-fill`)
  - `clip_archetype`: Target moment archetype bias
- Every clip planned or rendered for that campaign automatically enforces both Whop campaign compliance rules AND the extracted reference style profile.

### 6.3 1-Click Platform Setup Guides & Brand Kit Generation
- **Setup View Step 3 (Instagram)** and **Step 4 (YouTube)** feature dedicated `Open Guide & Generate Profile` buttons.
- Opens platform-tailored guides (Professional mode, public visibility, high quality upload, FB page linking, US country targeting, feature eligibility phone verification).
- Includes 1-click **Generate Fresh Profile Kit** calling `scripts/brand_kit_generator.py` with 1-click Copy buttons for Channel Name, Handle ideas, Bio, Keywords, and 5 hashtags, automatically saving to `config/brand_kit.md`.
