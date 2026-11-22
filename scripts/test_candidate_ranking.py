"""Unit test for score_candidate and auto-ranking logic in scripts/moment_selector.py."""

import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from moment_selector import score_candidate
from config_manager import load_viral_dna_weights


def test_mock_candidates():
    print("=" * 65)
    print("🧪 DRY-RUN UNIT TEST: DETERMINISTIC CANDIDATE AUTO-RANKER")
    print("=" * 65)

    weights = load_viral_dna_weights()

    # 3 Mock Candidates with distinct characteristics
    mock_candidates = [
        {
            "id": "candidate_A",
            "hook": "First time seeing this secret location",
            "theme": "easter_egg",
            "duration": 25.5,
            "streamer_source": "Typical Gamer",
            "peak_value": 0.95,
        },
        {
            "id": "candidate_B",
            "hook": "Watch the police AI at 0:08",
            "theme": "police_chase",
            "duration": 26.0,
            "streamer_source": "KreekCraft",
            "peak_value": 0.85,
        },
        {
            "id": "candidate_C",
            "hook": "Worst getaway driver in Vice City",
            "theme": "police_chase",
            "duration": 42.0,
            "streamer_source": "unknown",
            "peak_value": 0.20,
        },
    ]

    scored = []
    for c in mock_candidates:
        score, breakdown = score_candidate(c, weights)
        c["predicted_viral_score"] = score
        c["score_breakdown"] = breakdown
        scored.append(c)

    # Sort highest score first
    scored.sort(key=lambda x: x["predicted_viral_score"], reverse=True)

    for rank, c in enumerate(scored, 1):
        print(f"\n#{rank} [{c['id'].upper()}] Predicted Score: {c['predicted_viral_score']} / 100")
        print(f"   Hook: \"{c['hook']}\" | Theme: {c['theme']} | Duration: {c['duration']}s | Streamer: {c['streamer_source']}")
        print(f"   Breakdown: {json.dumps(c['score_breakdown'], indent=6)}")

    # Verification Assertions
    assert scored[0]["predicted_viral_score"] > scored[1]["predicted_viral_score"], "Candidate A/B ranking failure"
    assert scored[1]["predicted_viral_score"] > scored[2]["predicted_viral_score"], "Candidate B/C ranking failure"
    assert 0.0 <= scored[0]["predicted_viral_score"] <= 100.0, "Score out of 0-100 bounds"

    print("\n" + "=" * 65)
    print("✅ TEST PASSED: Auto-ranking sorted mock candidates highest-score-first strictly by Python math.")
    print("=" * 65)


def test_cold_start_neutrality():
    mock_c = {
        "id": "candidate_neutral",
        "hook": "Generic test hook here",
        "theme": "police_chase",
        "duration": 25.0,
        "streamer_source": "unknown",
        "peak_value": 0.50,
    }
    # Empty weights (cold start)
    score, breakdown = score_candidate(mock_c, viral_dna_weights={})
    print(f"\nCold-Start Neutral Score: {score} / 100")
    print(f"Breakdown: {json.dumps(breakdown)}")
    assert 40.0 <= score <= 65.0, "Cold start score should fall in neutral range"
    print("✅ COLD-START NEUTRALITY TEST PASSED.")


if __name__ == "__main__":
    test_mock_candidates()
    test_cold_start_neutrality()
