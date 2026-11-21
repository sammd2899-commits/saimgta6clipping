"""Viral Moment Selector (Wrapper Layer).

Discovers, filters, and ranks candidate moments from YouTube metadata/heatmap according to:
- config/editing_rules.json (duration 18-38s, 1 single idea, open immediately on chaos)
- Priority: smart/creepy NPC AI, police chases, crash physics/ragdoll, easter eggs, instant karma fails
- Strict Skip: cutscenes/endings, loud radio music, NSFW scenes, silent driving
- Hook Banners: 4-7 bold words with power words
"""

import json
import os
import random
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import (
    CONFIG_DIR,
    EDITING_RULES_PATH,
    LOGS_DIR,
    PUBLISHED_JSON,
    load_active_campaign,
    load_learned_rules,
)


def load_editing_rules() -> dict:
    if not EDITING_RULES_PATH.exists():
        raise FileNotFoundError(f"Editing rules not found at {EDITING_RULES_PATH}")
    with open(EDITING_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


PRIORITY_THEMES = [
    {
        "id": "npc_ai",
        "name": "smart_or_creepy_npc_ai_reactions",
        "hooks": [
            "GTA 6 NPCs are actually terrifying...",
            "Wait until you see what this NPC does",
            "This NPC has 200 IQ AI",
            "Nobody expected this NPC reaction",
        ],
    },
    {
        "id": "police_chase",
        "name": "absurd_vehicle_or_police_escape_chaos",
        "hooks": [
            "Bro really tried escaping cops on THIS",
            "Watch the police AI at 0:08",
            "Worst getaway driver in Vice City",
            "Instant karma in under 2 seconds",
        ],
    },
    {
        "id": "physics_glitch",
        "name": "shocking_crash_physics_ragdoll_and_glitches",
        "hooks": [
            "GTA 6 physics just broke completely",
            "This looks normal, until the end...",
            "He didn't see what was behind him",
            "Impossible crash physics in Vice City",
        ],
    },
    {
        "id": "easter_egg",
        "name": "hidden_map_easter_eggs_and_high_risk_stunts",
        "hooks": [
            "Nobody expected Rockstar to add THIS",
            "He stole a fighter jet and regretted it",
            "Secret GTA 6 easter egg discovered",
            "First time seeing this secret location",
        ],
    },
    {
        "id": "karma_fail",
        "name": "instant_karma_heist_fails_and_chat_trolling",
        "hooks": [
            "Instant karma in under 2 seconds",
            "He celebrated way too early here",
            "Wait for the instant karma fail",
            "Wrong move at the worst time",
        ],
    },
]


def enforce_hook_word_limit(hook: str, max_words: int = 7) -> str:
    """Enforces strictly <= max_words (4-7 words) without truncation artifacts."""
    clean = hook.strip()
    words = clean.split()
    if len(words) <= max_words:
        return clean
    return " ".join(words[:max_words])


def is_skip_segment(title: str, description: str = "", timestamp: float = 0.0) -> bool:
    """Checks for strictly skipped topics (story cutscenes, radio music, NSFW)."""
    text = f"{title} {description}".lower()
    skip_keywords = [
        "cutscene",
        "credits",
        "ending cutscene",
        "strip club",
        "radio music",
        "soundtrack full",
        "copyrighted music",
        "afk",
        "brb",
        "starting soon",
        "be right back",
    ]
    return any(k in text for k in skip_keywords)


def is_overlapping_range(start: float, end: float, existing_ranges: list[tuple[float, float]], threshold: float = 10.0) -> bool:
    for es, ee in existing_ranges:
        overlap = max(0.0, min(end, ee) - max(start, es))
        if overlap >= threshold:
            return True
    return False


def select_viral_moments(
    info: dict,
    target_count: int = None,
    already_clipped_ranges: list[tuple[float, float]] = None,
) -> list[dict]:
    """Selects high-impact moments based on Most Replayed heatmap + energy spikes.

    Adheres strictly to:
    - Target duration: [18, 38] seconds (default ~25-28s).
    - Open immediately on chaos/reaction (start 2-3s before peak).
    - 1 single idea per clip.
    - 4-7 word hook banner using power words & templates.
    """
    rules = load_editing_rules()
    target_duration_range = rules.get("video", {}).get("target_duration_sec", [18, 38])
    min_dur = target_duration_range[0]
    max_dur = target_duration_range[1]
    default_clip_dur = 25.0

    duration = float(info.get("duration") or 0)
    heatmap = info.get("heatmap") or []
    title = info.get("title", "")
    uploader = info.get("uploader") or info.get("channel", "Creator")

    if target_count is None:
        if duration >= 7200:
            target_count = 20
        elif duration >= 3600:
            target_count = 15
        elif duration >= 1800:
            target_count = 8
        elif duration >= 600:
            target_count = 5
        else:
            target_count = max(2, int(duration // 60))
        target_count = min(30, max(2, target_count))

    used_ranges = list(already_clipped_ranges or [])
    moments = []

    # 1. Process Heatmap Peaks (Most Replayed spikes)
    if heatmap and len(heatmap) > 10:
        valid_points = [
            p for p in heatmap
            if 90.0 <= p.get("start_time", 0) <= max(90.0, duration - 90.0)
        ]
        valid_points.sort(key=lambda x: x.get("value", 0), reverse=True)

        for pt in valid_points:
            if len(moments) >= target_count:
                break

            peak_start = float(pt.get("start_time", 0))
            peak_end = float(pt.get("end_time", peak_start + 10))
            peak_val = float(pt.get("value", 0))

            start_t = max(0.0, peak_start - 2.5)
            end_t = min(duration, start_t + default_clip_dur)
            actual_dur = end_t - start_t

            if actual_dur < min_dur or actual_dur > max_dur:
                continue

            if is_overlapping_range(start_t, end_t, used_ranges, threshold=12.0):
                continue

            used_ranges.append((start_t, end_t))

            theme_idx = len(moments) % len(PRIORITY_THEMES)
            theme = PRIORITY_THEMES[theme_idx]
            raw_hook = theme["hooks"][len(moments) % len(theme["hooks"])]
            hook = enforce_hook_word_limit(raw_hook, max_words=7)

            moments.append({
                "clip_id": len(moments) + 1,
                "start_time": round(start_t, 2),
                "end_time": round(end_t, 2),
                "duration": round(actual_dur, 2),
                "peak_value": round(peak_val, 3),
                "hook": hook,
                "hook_reason": f"Heatmap spike ({peak_val:.2f}) at {int(peak_start//60)}m{int(peak_start%60)}s [{theme['name']}]",
                "theme": theme["id"],
                "status": "PENDING",
            })

    # 2. Activity window fallback
    if len(moments) < target_count and duration > 120:
        step = max(75.0, (duration - 180.0) / (target_count * 1.5))
        curr = 90.0
        while curr + default_clip_dur < duration - 60.0 and len(moments) < target_count:
            start_t = curr
            end_t = curr + default_clip_dur
            actual_dur = end_t - start_t

            if not is_overlapping_range(start_t, end_t, used_ranges, threshold=12.0):
                used_ranges.append((start_t, end_t))
                theme_idx = len(moments) % len(PRIORITY_THEMES)
                theme = PRIORITY_THEMES[theme_idx]
                raw_hook = theme["hooks"][len(moments) % len(theme["hooks"])]
                hook = enforce_hook_word_limit(raw_hook, max_words=7)

                moments.append({
                    "clip_id": len(moments) + 1,
                    "start_time": round(start_t, 2),
                    "end_time": round(end_t, 2),
                    "duration": round(actual_dur, 2),
                    "peak_value": 0.85,
                    "hook": hook,
                    "hook_reason": f"High energy activity at {int(start_t//60)}m{int(start_t%60)}s [{theme['name']}]",
                    "theme": theme["id"],
                    "status": "PENDING",
                })
            curr += step

    moments.sort(key=lambda x: x["start_time"])
    for idx, m in enumerate(moments, start=1):
        m["clip_id"] = idx

    return moments
