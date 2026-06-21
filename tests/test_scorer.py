"""Tests for scorer.py."""
import pytest

from osint_triage.scorer import score_item, score_to_tier


# ── score_to_tier ─────────────────────────────────────────────────────────────

def test_tier_critical():
    assert score_to_tier(100) == "CRITICAL"
    assert score_to_tier(75) == "CRITICAL"


def test_tier_high():
    assert score_to_tier(74) == "HIGH"
    assert score_to_tier(50) == "HIGH"


def test_tier_medium():
    assert score_to_tier(49) == "MEDIUM"
    assert score_to_tier(25) == "MEDIUM"


def test_tier_low():
    assert score_to_tier(24) == "LOW"
    assert score_to_tier(0) == "LOW"


# ── score_item ────────────────────────────────────────────────────────────────

def _extraction(translation="", topic_tags=None, topic="Other", sensitivity="LOW"):
    return {
        "language": "Russian",
        "translation": translation,
        "claims": [],
        "entities": {"persons": [], "organizations": [], "locations": []},
        "topic": topic,
        "topic_tags": topic_tags or [],
        "sensitivity": sensitivity,
    }


def test_score_empty_extraction():
    score, matched = score_item(_extraction())
    assert score == 0
    assert matched == []


def test_score_icbm_keyword_hits_nuclear_area():
    score, matched = score_item(_extraction(translation="Russia tested a new icbm at high yield"))
    assert "Nuclear/WMD" in matched
    assert score > 0


def test_score_topic_tag_contributes():
    score, matched = score_item(_extraction(topic_tags=["nuclear", "ballistic missile", "deterrence"]))
    assert "Nuclear/WMD" in matched
    assert score > 0


def test_score_exact_topic_match_bonus():
    base, _ = score_item(_extraction(translation="nuclear warhead icbm", topic="Other"))
    bonus, _ = score_item(_extraction(translation="nuclear warhead icbm", topic="Nuclear/WMD"))
    # Topic match should not double-count if already in matched, but adds to score if new
    assert bonus >= base


def test_score_multi_area_bonus():
    single, matched_single = score_item(_extraction(translation="nuclear warhead"))
    multi, matched_multi = score_item(
        _extraction(translation="nuclear warhead hack breach cyber infrastructure attack")
    )
    # Multi-area match should produce higher score
    if len(matched_multi) > 1:
        assert multi > single


def test_score_capped_at_100():
    translation = " ".join([
        "nuclear warhead icbm deterrence plutonium enrichment",
        "hack cyber breach malware espionage infrastructure attack",
        "taiwan south china sea pla reunification independence",
        "semiconductor chips quantum dual-use export controls technology transfer",
    ])
    score, _ = score_item(_extraction(translation=translation, topic="Nuclear/WMD"))
    assert score <= 100


def test_score_taiwan_keywords():
    score, matched = score_item(_extraction(translation="pla exercises in taiwan strait"))
    assert "Taiwan/South China Sea" in matched
    assert score > 0


def test_score_ukraine_nato_keywords():
    score, matched = score_item(_extraction(translation="nato eastern flank escalation ukraine kyiv"))
    assert "Ukraine/NATO" in matched


def test_score_sanctions_keywords():
    score, matched = score_item(_extraction(topic_tags=["sanctions", "export controls"]))
    assert "Sanctions/Trade" in matched


def test_score_low_priority_domestic():
    score, matched = score_item(_extraction(
        translation="Russia approves annual domestic budget for the next fiscal year"
    ))
    assert score < 25


def test_score_matched_areas_list():
    _, matched = score_item(_extraction(translation="nuclear warhead icbm"))
    assert isinstance(matched, list)
    assert all(isinstance(a, str) for a in matched)
