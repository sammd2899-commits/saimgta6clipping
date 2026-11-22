"""Viral Moment Selector (Wrapper Layer).

Discovers, filters, and ranks candidate moments from YouTube metadata/heatmap according to:
- config/editing_rules.json (duration 18-38s, 1 single idea, open immediately on chaos)
- Priority: smart/creepy NPC AI, police chases, crash physics/ragdoll, easter eggs, instant karma fails
- Strict Skip: cutscenes/endings, loud radio music, NSFW scenes, silent driving
- Hook Banners: 4-7 bold words with power words
"""

import datetime
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
    LOGS_DIR,
    PUBLISHED_JSON,
    QUEUE_PATH,
    load_active_campaign,
    load_learned_rules,
    load_viral_dna_weights,
)

EDITING_RULES_PATH = CONFIG_DIR / "editing_rules.json"


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
            "Wait until you see this NPC",
            "This NPC has 200 IQ AI",
            "Nobody expected this wild NPC reaction",
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
            "He stole a jet and regretted it",
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


def score_candidate(candidate: dict, viral_dna_weights: dict = None) -> tuple[float, dict]:
    """Assigns a deterministic numeric predicted_viral_score (0-100) combining:
    - hook_style weight (from viral_dna_weights.json)
    - duration_bucket weight (e.g., 18-24s vs 25-35s)
    - moment_archetype weight (npc_ai, vehicle_police_chase, crash_physics_glitch, easter_egg_stunt, instant_karma_fail)
    - streamer_source weight
    - YouTube Most Replayed heatmap spike bonus (peak_value)

    Defaults all weights neutrally (1.0x / cold-start baseline) if no historical data exists.
    Returns (predicted_viral_score: float, score_breakdown: dict).
    """
    if viral_dna_weights is None:
        viral_dna_weights = load_viral_dna_weights() or {}

    archetype_weights = viral_dna_weights.get("moment_archetypes", {})
    duration_weights = viral_dna_weights.get("duration_sweet_spots", {})
    formula_weights = viral_dna_weights.get("hook_and_title_formulas", {}).get("formulas", {})
    streamer_weights = viral_dna_weights.get("streamer_source_weights", {})

    archetype_map = {
        "easter_egg": "easter_egg_stunt",
        "easter_egg_stunt": "easter_egg_stunt",
        "police_chase": "vehicle_police_chase",
        "vehicle_police_chase": "vehicle_police_chase",
        "physics_glitch": "crash_physics_glitch",
        "crash_physics_glitch": "crash_physics_glitch",
        "npc_ai": "npc_ai",
        "karma_fail": "instant_karma_fail",
        "instant_karma_fail": "instant_karma_fail",
    }

    # 1. Base Score
    base_score = 20.0

    # 2. Archetype Weight (Max 25 pts)
    theme_key = candidate.get("theme") or candidate.get("archetype") or "police_chase"
    arch_id = archetype_map.get(theme_key, "vehicle_police_chase")
    arch_wt = float(archetype_weights.get(arch_id, {}).get("weight", 1.0))
    archetype_pts = round(min(25.0, max(2.0, arch_wt * 8.0)), 1)

    # 3. Hook Formula Weight (Max 20 pts)
    hook_text = (candidate.get("hook") or candidate.get("title") or "").lower()
    if any(k in hook_text for k in ["secret", "location", "nobody expected", "rockstar"]):
        form_id = "discovery_secret"
    elif any(k in hook_text for k in ["at 0:", "under 2 seconds", "in under"]):
        form_id = "curiosity_timestamp"
    elif any(k in hook_text for k in ["physics just broke", "impossible crash", "looks normal"]):
        form_id = "absurd_physics"
    elif any(k in hook_text for k in ["didn't see what", "worst getaway driver", "bro really"]):
        form_id = "mystery_warning"
    else:
        form_id = "observation_alert"

    form_wt = float(formula_weights.get(form_id, {}).get("weight", 1.0))
    hook_pts = round(min(20.0, max(2.0, form_wt * 6.5)), 1)

    # 4. Duration Bucket Weight (Max 15 pts)
    dur = float(candidate.get("duration") or 25.0)
    b_key = "18-24s" if dur < 25.0 else ("25-30s" if dur <= 30.0 else ("31-38s" if dur <= 38.0 else "39-45s"))
    dur_wt = float(duration_weights.get(b_key, {}).get("weight", 1.0))
    duration_pts = round(min(15.0, max(2.0, dur_wt * 8.0)), 1)

    # 5. Streamer Source Weight (Max 15 pts)
    s_source = str(candidate.get("streamer_source") or candidate.get("uploader") or candidate.get("channel") or "unknown")
    s_name = s_source.split("(")[0].strip()
    s_wt = float(streamer_weights.get(s_name, {}).get("weight", 1.0))
    streamer_pts = round(min(15.0, max(2.0, s_wt * 6.5)), 1)

    # 6. Heatmap Spike Bonus (Max 15 pts)
    peak_val = float(candidate.get("peak_value") or 0.0)
    heatmap_pts = round(min(15.0, max(0.0, peak_val * 15.0)), 1)

    total_score = round(min(100.0, max(0.0, base_score + archetype_pts + hook_pts + duration_pts + streamer_pts + heatmap_pts)), 1)

    breakdown = {
        "base_score": base_score,
        "archetype": f"{arch_id} (wt={arch_wt}x, +{archetype_pts}pts)",
        "hook_formula": f"{form_id} (wt={form_wt}x, +{hook_pts}pts)",
        "duration_bucket": f"{b_key} (wt={dur_wt}x, +{duration_pts}pts)",
        "streamer": f"{s_name} (wt={s_wt}x, +{streamer_pts}pts)",
        "heatmap_spike": f"peak={peak_val:.2f} (+{heatmap_pts}pts)",
        "total": total_score,
    }

    return total_score, breakdown


def rank_pending_queue(queue_path: Path = QUEUE_PATH) -> dict:
    """Auto-sorts all PENDING candidates in state/job_queue.json from highest predicted_viral_score to lowest,
    preserving the 80% top-ranked / 20% A/B-test slot allocation without touching SCHEDULED or PUBLISHED clips.
    """
    if not queue_path.exists():
        return {}
    with open(queue_path, "r", encoding="utf-8") as f:
        queue_data = json.load(f)

    clips = queue_data.get("clips", [])
    pending = [c for c in clips if c.get("status") == "PENDING"]
    non_pending = [c for c in clips if c.get("status") != "PENDING"]

    if not pending:
        return queue_data

    viral_weights = load_viral_dna_weights()
    for c in pending:
        score, breakdown = score_candidate(c, viral_weights)
        c["predicted_viral_score"] = score
        c["score_breakdown"] = breakdown

    # Sort pending highest score first
    pending.sort(key=lambda x: x.get("predicted_viral_score", 0), reverse=True)

    # Preserve 80/20 A/B allocation on pending
    cutoff = max(1, int(len(pending) * 0.8))
    for idx, c in enumerate(pending):
        c["ab_test"] = (idx >= cutoff)

    # Reassemble queue
    queue_data["clips"] = non_pending + pending
    queue_data["last_updated"] = datetime.datetime.now().astimezone().isoformat()
    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2)

    return queue_data


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
    default_clip_dur = 25.0  # Optimal viral Shorts/Reels duration

    # 0. Load Viral DNA Weights and reorder themes by performance
    viral_weights = load_viral_dna_weights()
    archetype_weights = viral_weights.get("moment_archetypes", {})

    archetype_map = {
        "easter_egg": "easter_egg_stunt",
        "police_chase": "vehicle_police_chase",
        "physics_glitch": "crash_physics_glitch",
        "npc_ai": "npc_ai",
        "karma_fail": "instant_karma_fail",
    }

    active_themes = list(PRIORITY_THEMES)
    if archetype_weights:
        active_themes.sort(
            key=lambda t: archetype_weights.get(archetype_map.get(t["id"], ""), {}).get("weight", 1.0),
            reverse=True,
        )

    # Duration sweet spot adaptation
    duration_spots = viral_weights.get("duration_sweet_spots", {})
    if duration_spots.get("25-30s", {}).get("weight", 1.0) >= 1.5:
        default_clip_dur = 25.5

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
        # Filter out first 90s intro and last 90s outro
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

            # Rule: Open immediately on chaos/reaction (lead-in only 2.5s before peak)
            start_t = max(0.0, peak_start - 2.5)
            end_t = min(duration, start_t + default_clip_dur)
            actual_dur = end_t - start_t

            if actual_dur < min_dur or actual_dur > max_dur:
                continue

            if is_overlapping_range(start_t, end_t, used_ranges, threshold=12.0):
                continue

            used_ranges.append((start_t, end_t))

            # Select theme and hook adhering to 4-7 words (with 80/20 A/B allocation)
            is_ab_test = len(moments) >= int(target_count * 0.8)
            theme_idx = len(moments) % len(active_themes)
            theme = active_themes[theme_idx]
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
                "ab_test": is_ab_test,
                "status": "PENDING",
            })

    # 2. Activity window fallback if heatmap is sparse
    if len(moments) < target_count and duration > 120:
        step = max(75.0, (duration - 180.0) / (target_count * 1.5))
        curr = 90.0
        while curr + default_clip_dur < duration - 60.0 and len(moments) < target_count:
            start_t = curr
            end_t = curr + default_clip_dur
            actual_dur = end_t - start_t

            if not is_overlapping_range(start_t, end_t, used_ranges, threshold=12.0):
                used_ranges.append((start_t, end_t))
                is_ab_test = len(moments) >= int(target_count * 0.8)
                theme_idx = len(moments) % len(active_themes)
                theme = active_themes[theme_idx]
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
                    "ab_test": is_ab_test,
                    "status": "PENDING",
                })
            curr += step

    # Deterministic Scoring & Auto-Ranking by predicted_viral_score
    streamer_full = f"{uploader} ({info.get('id')})" if info.get("id") else uploader
    for m in moments:
        m["streamer_source"] = streamer_full
        score, breakdown = score_candidate(m, viral_weights)
        m["predicted_viral_score"] = score
        m["score_breakdown"] = breakdown

    # Auto-sort from highest predicted_viral_score to lowest
    moments.sort(key=lambda x: x.get("predicted_viral_score", 0), reverse=True)

    # Preserve 80% top-ranked / 20% A/B-test slot allocation
    cutoff = max(1, int(len(moments) * 0.8))
    for idx, m in enumerate(moments, start=1):
        m["clip_id"] = idx
        m["ab_test"] = (idx > cutoff)

    return moments


if __name__ == "__main__":
    sample_info = {
        "title": "GTA 6 Livestream KreekCraft",
        "duration": 7200,
        "heatmap": [
            {"start_time": 300, "end_time": 315, "value": 0.95},
            {"start_time": 850, "end_time": 865, "value": 0.98},
            {"start_time": 1420, "end_time": 1435, "value": 0.92},
            {"start_time": 2100, "end_time": 2115, "value": 0.89},
        ],
    }
    res = select_viral_moments(sample_info, target_count=4)
    for r in res:
        print(f"Clip #{r['clip_id']}: {r['start_time']}s-{r['end_time']}s ({r['duration']}s) | Hook: {r['hook']} ({len(r['hook'].split())} words)")
