"""Deterministic relevance scorer.

No Claude — pure keyword matching against analyst-defined interest areas.
Scores are reproducible and auditable without an API call.
"""
from __future__ import annotations

from osint_triage.config import INTEREST_AREAS, PRIORITY_TIERS


def score_item(extraction: dict) -> tuple[int, list[str]]:
    """Score an extracted item against analyst interest areas.

    Searches:
      - extraction["translation"] (English text)
      - extraction["topic_tags"] (Claude-assigned keywords)
      - extraction["topic"] (Claude-assigned primary topic)

    Returns (priority_score: int, matched_areas: list[str]).
    priority_score is capped at 100.
    """
    translation = (extraction.get("translation") or "").lower()
    topic_tags = " ".join(extraction.get("topic_tags") or []).lower()
    search_text = translation + " " + topic_tags

    score = 0
    matched: list[str] = []

    for area, cfg in INTEREST_AREAS.items():
        hits = sum(1 for kw in cfg["keywords"] if kw.lower() in search_text)
        if hits > 0:
            # Cap per-area contribution at 3 keyword hits
            score += cfg["weight"] * min(hits, 3)
            matched.append(area)

    # Topic exact-match bonus (Claude's own classification)
    topic = extraction.get("topic", "")
    if topic in INTEREST_AREAS and topic not in matched:
        score += INTEREST_AREAS[topic]["weight"]
        matched.append(topic)

    # Multi-area bonus: hitting >1 area suggests cross-domain significance
    if len(matched) > 1:
        score = int(score * 1.25)

    return min(100, score), matched


def score_to_tier(score: int) -> str:
    """Map a numeric score to a priority tier label."""
    for tier, threshold in PRIORITY_TIERS:
        if score >= threshold:
            return tier
    return "LOW"
