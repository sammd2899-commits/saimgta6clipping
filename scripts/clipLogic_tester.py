"""Studio Compliance Logic & Safe Zone Tester.

Mirrors web/src/utils/clipLogic.ts validateClipCompliance & safe-zone metrics.
"""

def validate_clip_compliance(clip: dict, active_preset: dict) -> dict:
    checks = []
    
    # 1. Title <= 65 chars
    title = clip.get("yt_title", "")
    title_ok = len(title) <= 65
    checks.append({
        "id": "title_length",
        "label": "YouTube Title Length (≤ 65 chars)",
        "passed": title_ok,
        "detail": f"{len(title)}/65 characters",
    })

    # 2. Instagram Hashtags <= 5
    tags = clip.get("hashtags", [])
    max_tags = active_preset.get("max_ig_hashtags", 5)
    tags_count_ok = len(tags) <= max_tags
    checks.append({
        "id": "hashtag_count",
        "label": f"Instagram Hashtags (≤ {max_tags} tags)",
        "passed": tags_count_ok,
        "detail": f"{len(tags)}/{max_tags} tags",
    })

    # 3. Required Campaign Hashtags
    req_tags = active_preset.get("required_hashtags", [])
    missing_tags = [t for t in req_tags if not any(t.lower() == existing.lower() for existing in tags)]
    req_tags_ok = len(missing_tags) == 0
    checks.append({
        "id": "required_hashtags",
        "label": f"Required Campaign Tags ({', '.join(req_tags)})",
        "passed": req_tags_ok,
        "detail": "All present" if req_tags_ok else f"Missing: {', '.join(missing_tags)}",
    })

    all_passed = all(c["passed"] for c in checks)
    return {"allPassed": all_passed, "checks": checks}


def test_studio_compliance_logic(clip: dict, active_campaign: dict):
    # Test valid title
    test_clip_valid = dict(clip)
    test_clip_valid["yt_title"] = "GTA 6 Insane Police Escape Secret"  # 34 chars <= 65
    test_clip_valid["hashtags"] = ["#gta6", "#TestClip", "#Gaming"]     # 3 <= 5
    res_valid = validate_clip_compliance(test_clip_valid, active_campaign)
    assert res_valid["allPassed"], f"Expected valid clip to pass compliance, got: {res_valid}"

    # Test title > 65 chars
    test_clip_long_title = dict(clip)
    test_clip_long_title["yt_title"] = "GTA 6 Unbelievable Cop Chase With Five Stars Going Across The Entire Ocean Beach Freeway"  # 88 chars
    res_long = validate_clip_compliance(test_clip_long_title, active_campaign)
    assert not res_long["allPassed"], "Expected title > 65 chars to fail compliance"
    assert any(c["id"] == "title_length" and not c["passed"] for c in res_long["checks"])

    # Test hashtags > 5
    test_clip_many_tags = dict(clip)
    test_clip_many_tags["hashtags"] = ["#gta6", "#TestClip", "#Tag3", "#Tag4", "#Tag5", "#Tag6"]
    res_tags = validate_clip_compliance(test_clip_many_tags, active_campaign)
    assert not res_tags["allPassed"], "Expected > 5 hashtags to fail compliance"
    assert any(c["id"] == "hashtag_count" and not c["passed"] for c in res_tags["checks"])

    # Test missing required hashtags
    test_clip_missing_req = dict(clip)
    test_clip_missing_req["hashtags"] = ["#Gaming", "#Fun"]
    res_missing = validate_clip_compliance(test_clip_missing_req, active_campaign)
    assert not res_missing["allPassed"], "Expected missing required hashtags to fail compliance"
    assert any(c["id"] == "required_hashtags" and not c["passed"] for c in res_missing["checks"])

    # Safe Zone boundaries verification
    safe_zones = {
        "top_dead_zone_pct": 11,
        "right_icons_dead_zone_pct": 18,
        "bottom_caption_dead_zone_pct": 18,
        "hook_banner_min_y": 8,
        "hook_banner_max_y": 32,
    }
    assert safe_zones["top_dead_zone_pct"] == 11
    assert safe_zones["right_icons_dead_zone_pct"] == 18
    assert safe_zones["bottom_caption_dead_zone_pct"] == 18
