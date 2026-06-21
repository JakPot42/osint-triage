"""Claude Haiku extraction: translate + structured entity/claim extraction.

Sends foreign-language article text to Claude and returns a structured dict.
All Claude calls are isolated here so tests can mock this module.
"""
from __future__ import annotations

import json
import re

from osint_triage.config import CLAUDE_MODEL, VALID_TOPICS

_EXTRACTION_SYSTEM = f"""You are a senior intelligence analyst supporting foreign-language OSINT document triage.
You will receive the title and body of a news article in a foreign language.

Respond with ONLY a valid JSON object. No prose before or after. No markdown fences.

Required format:
{{
  "language": "<detected language, e.g. Russian, Chinese, Arabic, Spanish, Persian>",
  "translation": "<English translation: headline + 2-3 sentence accurate summary>",
  "claims": ["<top verifiable factual claim 1 in English>", "<claim 2>", "<claim 3>"],
  "entities": {{
    "persons": ["<name>"],
    "organizations": ["<org>"],
    "locations": ["<place>"]
  }},
  "topic": "<primary topic — MUST be one of: {', '.join(VALID_TOPICS)}>",
  "topic_tags": ["<2-4 lowercase English keywords for relevance scoring>"],
  "sensitivity": "<LOW | MEDIUM | HIGH | CRITICAL>"
}}

Rules:
- Output ONLY the JSON object
- claims: top 3 specific, verifiable factual assertions from the text
- topic: single best-fitting category from the allowed list
- topic_tags: 2-4 lowercase English keywords useful for keyword matching
- translation: accurate summary — note the outlet's framing without amplifying propaganda
- If text is very short or unclear, do your best with available content
- sensitivity: your own analytical assessment of how urgent this is for a human linguist"""

_FALLBACK_EXTRACTION = {
    "language": "Unknown",
    "translation": "[Extraction failed — manual review required]",
    "claims": [],
    "entities": {"persons": [], "organizations": [], "locations": []},
    "topic": "Other",
    "topic_tags": [],
    "sensitivity": "LOW",
}


def parse_extraction(raw: str) -> dict | None:
    """Parse Claude's JSON response. Returns None if unparseable."""
    # Strip markdown fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _validate(data: dict) -> dict:
    """Ensure required keys exist and topic is valid."""
    if data.get("topic") not in VALID_TOPICS:
        data["topic"] = "Other"
    for key in ("language", "translation", "claims", "entities", "topic", "topic_tags", "sensitivity"):
        if key not in data:
            data[key] = _FALLBACK_EXTRACTION[key]
    if not isinstance(data.get("entities"), dict):
        data["entities"] = {"persons": [], "organizations": [], "locations": []}
    return data


def extract_item(title: str, body: str, model: str = CLAUDE_MODEL) -> dict:
    """Call Claude to translate and extract claims/entities from a foreign-language item.

    Returns a structured extraction dict. On Claude error, returns fallback dict.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise ImportError("anthropic not installed — run: pip install anthropic") from exc

    text = f"TITLE: {title}\n\nBODY: {body}" if body else f"TITLE: {title}"

    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=model,
            max_tokens=800,
            system=_EXTRACTION_SYSTEM,
            messages=[{"role": "user", "content": text}],
        )
        raw = resp.content[0].text
    except Exception:
        return dict(_FALLBACK_EXTRACTION)

    parsed = parse_extraction(raw)
    if parsed is None:
        return dict(_FALLBACK_EXTRACTION)

    return _validate(parsed)
