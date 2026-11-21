# Learned Rules & Pacing Directives

*Keep concise and bulleted for lightweight LLM ingestion.*

## Visual Layout & Universal Safe-Zone Blueprint (1080x1920, 9:16)
- **Universal Safe Box:** 890x1250 px (x = 60..940, y = 250..1490). Zero text or facecam covered by Instagram Reels or YouTube Shorts UI buttons.
- **Top UI Dead Zone:** Keep y = 0..250 px completely clear.
- **Hook Banner (0.0s – 2.5s only):** Positioned at y = 290 px. Exactly 4–7 bold words, centered, dark rounded pill background with clean outline.
- **Top 35% (1080x672 px):** Streamer Facecam zoomed & centered on reaction.
- **Bottom 65% (1080x1248 px):** GTA 6 Gameplay center-cropped on action (or full-bleed blurred vertical fill fallback with NO black bars).
- **Dynamic Word Captions:** Strictly positioned in y = 1150–1320 px (MarginV = 650 from bottom, 68px Montserrat/Anton/Arial Bold, 5px black outline, active word highlight in `#FFE600` yellow pop, 2–4 words per chunk, clear of 140px right dead zone).
- **Bottom UI Dead Zone:** Keep y = 1490..1920 px (430 px) completely clear for username, subscribe button, audio title, and platform description overlay.

## Audio & Video Technical Specifications
- **Format:** 1080x1920, 60fps, Codec libx264, Bitrate 6 Mbps, yuv420p, +faststart.
- **Duration Rules:** Target 18–38 seconds (optimal for Shorts/Reels algorithm retention); hard bounds 12–55 seconds.
- **Audio Normalization:** Silence trimming > 0.6s and FFmpeg `loudnorm=I=-14:TP=-1.5:LRA=11` (-14 LUFS standard).
- **Zero Third-Party Watermarks:** External watermarks (TikTok, etc.) strictly forbidden.

## Viral Moment Selection & Hook Blueprint
- **Core Principle:** 1 single idea/payoff per clip, opening IMMEDIATELY on the chaos or reaction (no slow walkup or menu waiting).
- **Prioritize:** (1) smart or creepy NPC AI reactions, (2) absurd vehicle or police escape chaos, (3) shocking crash physics/ragdoll and glitches, (4) hidden map easter eggs and high-risk stunts, (5) instant karma heist fails and chat trolling.
- **Strictly Skip:** Story cutscenes and endings (copyright risk), loud licensed radio songs (Content ID risk), NSFW scenes, silent driving.
- **Power Words:** Wait, Nobody, Actually, Instant, Secret, Terrifying, Impossible, Broke, Wrong, First time.

## Platform Metadata & Compliance Guardrails
- **Instagram Reels:**
  * Maximum 5 hashtags total (required campaign tags + discoverability tags).
  * 1 DM-share trigger line.
  * Mandatory credit & channel tag.
  * Cover frame: 1080x1920 centered reaction frame (1:1 profile grid safe, y = 420..1500).
- **YouTube Shorts:**
  * Curiosity-gap title strictly <= 65 characters including `#Shorts`.
  * Mandatory credit and channel tag in description.
  * Description tags: `#GTA6 #GrandTheftAutoVI #Shorts`.
  * Engaging English first / pinned comment for discussion.
- **Dynamic Campaign Overrides:** Always pull mandatory credit, channel tag, and required campaign tags dynamically from `config/active_campaign.json`.

## Scheduling & Spacing
- **Awake Schedule:** 5 clips/day strictly during awake hours, mapped accurately to UTC for Zernio v1 API scheduling (`scheduledFor`). Zero overnight posts.
- **Chunked Queue State Machine:** `state/job_queue.json` processes 1 clip at a time atomically with hard ffprobe verification before scheduling, immediately releasing temp disk space.
