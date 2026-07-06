"""Tests for extractor.py.

Mocking target updated: extract_item now calls the shared
osint_triage.claude_client.call_claude() wrapper instead of constructing its
own anthropic.Anthropic() client, so tests patch "osint_triage.extractor.call_claude"
directly and return plain response strings.
"""
import json
from unittest.mock import patch

import pytest

from osint_triage.extractor import extract_item, parse_extraction, _validate


# ── parse_extraction ──────────────────────────────────────────────────────────

def test_parse_extraction_clean_json():
    raw = json.dumps({"language": "Russian", "translation": "Test"})
    result = parse_extraction(raw)
    assert result["language"] == "Russian"


def test_parse_extraction_strips_markdown_fences():
    raw = "```json\n{\"language\": \"Russian\"}\n```"
    result = parse_extraction(raw)
    assert result is not None
    assert result["language"] == "Russian"


def test_parse_extraction_invalid_json_returns_none():
    result = parse_extraction("not valid json at all {{{")
    assert result is None


def test_parse_extraction_empty_string_returns_none():
    result = parse_extraction("")
    assert result is None


# ── _validate ─────────────────────────────────────────────────────────────────

def test_validate_fills_missing_keys():
    result = _validate({"language": "Russian"})
    for key in ("translation", "claims", "entities", "topic", "topic_tags", "sensitivity"):
        assert key in result


def test_validate_invalid_topic_replaced():
    result = _validate({"topic": "Classified Weapons Plans"})
    assert result["topic"] == "Other"


def test_validate_valid_topic_preserved():
    result = _validate({"topic": "Nuclear/WMD"})
    assert result["topic"] == "Nuclear/WMD"


def test_validate_bad_entities_replaced():
    result = _validate({"entities": "not a dict"})
    assert isinstance(result["entities"], dict)
    assert "persons" in result["entities"]


# ── extract_item ──────────────────────────────────────────────────────────────

_GOOD_EXTRACTION = {
    "language": "Russian",
    "translation": "Russia tested a new ICBM at Plesetsk.",
    "claims": ["Russia tested Sarmat ICBM"],
    "entities": {"persons": [], "organizations": ["MoD"], "locations": ["Plesetsk"]},
    "topic": "Nuclear/WMD",
    "topic_tags": ["nuclear", "icbm"],
    "sensitivity": "CRITICAL",
}


def test_extract_item_happy_path():
    with patch("osint_triage.extractor.call_claude", return_value=json.dumps(_GOOD_EXTRACTION)):
        result = extract_item("Россия испытала МБР", "Текст статьи")
    assert result["language"] == "Russian"
    assert result["topic"] == "Nuclear/WMD"
    assert "Plesetsk" in result["entities"]["locations"]


def test_extract_item_invalid_json_falls_back():
    with patch("osint_triage.extractor.call_claude", return_value="This is not JSON at all."):
        result = extract_item("Some title", "Some body")
    assert result["language"] == "Unknown"
    assert result["topic"] == "Other"
    assert result["translation"] == "[Extraction failed — manual review required]"


def test_extract_item_api_error_falls_back():
    with patch("osint_triage.extractor.call_claude", side_effect=Exception("API timeout")):
        result = extract_item("Title", "Body")
    assert result["topic"] == "Other"
    assert result["claims"] == []


def test_extract_item_with_markdown_fences():
    fenced = f"```json\n{json.dumps(_GOOD_EXTRACTION)}\n```"
    with patch("osint_triage.extractor.call_claude", return_value=fenced):
        result = extract_item("Title", "Body")
    assert result["topic"] == "Nuclear/WMD"


def test_extract_item_empty_title_body():
    with patch("osint_triage.extractor.call_claude", return_value=json.dumps(_GOOD_EXTRACTION)):
        result = extract_item("", "")
    assert result is not None
