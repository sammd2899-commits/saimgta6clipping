"""Multi-Reference Campaign Style Analyzer.

Inspects reference video URLs, Google Drive links, and style notes to extract
a coherent Reference Style Profile (pacing, hook style, caption tone, layout, archetype)
using Google Gemini API (or heuristic analysis fallback).
"""

import json
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from gemini_backend import call_gemini, has_gemini_api_key


def analyze_references(references: list[str], campaign_name: str = "Campaign") -> dict:
    """Analyzes a list of reference URLs, drive links, or style notes.

    Returns a structured reference_style_profile dictionary.
    """
    cleaned_refs = [r.strip() for r in references if isinstance(r, str) and r.strip()]
    if not cleaned_refs:
        return {
            "pacing": "Fast-paced 20-24s sweet spot with chaos opening in first 0.8s",
            "hook_style": "High-contrast 4-7 word bold question banner at Y=290px",
            "caption_tone": "High-energy reaction with #FFE600 active word pop",
            "layout": "split-35-65",
            "clip_archetype": "Police Chase",
            "extracted_keywords": ["GTA6", "ViceCity", "Action"],
            "summary": "Standard high-retention 9:16 viral gaming format.",
            "reference_count": 0,
        }

    ref_text = "\n".join([f"- Reference {i+1}: {ref}" for i, ref in enumerate(cleaned_refs)])

    # Try Gemini API if key is available
    if has_gemini_api_key():
        prompt = (
            f"Analyze these short-form video reference links, clip examples, or style notes for the campaign '{campaign_name}':\n"
            f"{ref_text}\n\n"
            f"Extract a structured short-form video style profile for 9:16 vertical clips. "
            f"Return strictly valid JSON with these keys:\n"
            f"1. \"pacing\": pacing description (e.g., 'Rapid 0.8s cuts opening directly on vehicle chaos')\n"
            f"2. \"hook_style\": hook banner style (e.g., 'Curiosity-driven high stakes banner at Y=290px')\n"
            f"3. \"caption_tone\": caption feel (e.g., 'High-energy gamer reaction, punchy uppercase words')\n"
            f"4. \"layout\": strictly either 'split-35-65' or 'blurred-fill'\n"
            f"5. \"clip_archetype\": strictly one of ['Police Chase', 'Crash Physics', 'NPC AI', 'Instant Fail', 'Map Secret']\n"
            f"6. \"extracted_keywords\": list of 4-6 style tags\n"
            f"7. \"summary\": 1-2 sentence summary of this reference aesthetic\n"
            f"Return JSON only, no markdown ticks, no extra text."
        )
        try:
            raw = call_gemini(
                prompt=prompt,
                system_instruction="You are a professional video editor specializing in viral 9:16 Reels and YouTube Shorts algorithms.",
                temperature=0.4,
            )
            if raw:
                clean_json = raw.strip()
                if clean_json.startswith("```"):
                    clean_json = re.sub(r"^```(?:json)?\s*", "", clean_json)
                    clean_json = re.sub(r"\s*```$", "", clean_json)
                parsed = json.loads(clean_json)
                if "pacing" in parsed and "layout" in parsed:
                    parsed["reference_count"] = len(cleaned_refs)
                    return parsed
        except Exception as e:
            print(f"[Reference Analyzer] Gemini analysis notice: {e}")

    # Deterministic Heuristic Fallback
    combined = " ".join(cleaned_refs).lower()

    # Detect layout
    layout = "split-35-65"
    if "full bleed" in combined or "blurred" in combined or "gameplay only" in combined or "no face" in combined:
        layout = "blurred-fill"

    # Detect archetype
    archetype = "Police Chase"
    if "physics" in combined or "glitch" in combined or "ragdoll" in combined:
        archetype = "Crash Physics"
    elif "npc" in combined or "ai" in combined or "dialogue" in combined or "pedestrian" in combined:
        archetype = "NPC AI"
    elif "fail" in combined or "karma" in combined or "bloopers" in combined:
        archetype = "Instant Fail"
    elif "secret" in combined or "easter egg" in combined or "stunt" in combined or "map" in combined:
        archetype = "Map Secret"

    # Hook style & pacing heuristics
    if "question" in combined or "curiosity" in combined:
        hook_style = "Provocative question banner at Y=290px ('Wait till you see what happened...')"
    elif "shock" in combined or "loud" in combined or "chaos" in combined:
        hook_style = "High-energy shock banner at Y=290px with active power words"
    else:
        hook_style = "Punchy 4-7 word bold safe-zone banner in high-contrast #FFE600 / white"

    if "fast" in combined or "rapid" in combined or "quick" in combined:
        pacing = "Ultra-fast cuts (18-22s duration) with reaction spike in first 0.6s"
    elif "cinematic" in combined or "story" in combined:
        pacing = "Controlled 25-30s narrative buildup culminating in climax"
    else:
        pacing = "Optimal 20-24s sweet spot with instant visual action opening"

    summary = (
        f"Multi-reference analysis ({len(cleaned_refs)} sources): Targeted {archetype} archetype "
        f"with {layout} layout and high-contrast safe zone hooks."
    )

    return {
        "pacing": pacing,
        "hook_style": hook_style,
        "caption_tone": "High-contrast dynamic ASS subtitles with #FFE600 highlight",
        "layout": layout,
        "clip_archetype": archetype,
        "extracted_keywords": ["GTA6", "Viral", archetype.replace(" ", ""), layout],
        "summary": summary,
        "reference_count": len(cleaned_refs),
    }
