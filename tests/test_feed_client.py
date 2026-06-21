"""Tests for feed_client.py."""
from unittest.mock import MagicMock, patch

import pytest

from osint_triage.feed_client import _clean_html, _url_hash, fetch_feed, fetch_all_feeds


# ── helpers ───────────────────────────────────────────────────────────────────

def test_clean_html_strips_tags():
    assert _clean_html("<b>hello</b> <i>world</i>") == "hello world"


def test_clean_html_decodes_entities():
    assert _clean_html("a &amp; b") == "a & b"


def test_clean_html_empty():
    assert _clean_html("") == ""
    assert _clean_html(None) == ""


def test_url_hash_deterministic():
    h1 = _url_hash("https://example.com/article/1")
    h2 = _url_hash("https://example.com/article/1")
    assert h1 == h2 and len(h1) == 32


def test_url_hash_different_urls():
    assert _url_hash("https://a.com/1") != _url_hash("https://a.com/2")


# ── fetch_feed ────────────────────────────────────────────────────────────────

def _make_entry(url, title, summary="body text"):
    entry = MagicMock()
    entry.link = url
    entry.title = title
    entry.summary = summary
    entry.content = []
    entry.published_parsed = (2026, 6, 1, 12, 0, 0, 0, 0, 0)
    return entry


def test_fetch_feed_returns_items():
    mock_feed = MagicMock()
    mock_feed.entries = [
        _make_entry("https://tass.ru/1", "Заголовок один"),
        _make_entry("https://tass.ru/2", "Заголовок два"),
    ]
    with patch("feedparser.parse", return_value=mock_feed):
        items = fetch_feed("TASS Russian", "https://tass.ru/rss", "Russian", "state_media")
    assert len(items) == 2
    assert items[0]["source_name"] == "TASS Russian"
    assert items[0]["language"] == "Russian"
    assert items[0]["outlet"] == "state_media"


def test_fetch_feed_deduplicates_within_feed():
    mock_feed = MagicMock()
    mock_feed.entries = [
        _make_entry("https://tass.ru/1", "Title A"),
        _make_entry("https://tass.ru/1", "Title A duplicate"),
    ]
    with patch("feedparser.parse", return_value=mock_feed):
        items = fetch_feed("TASS Russian", "https://tass.ru/rss", "Russian", "state_media")
    assert len(items) == 1


def test_fetch_feed_skips_entries_without_url():
    entry_no_url = MagicMock()
    entry_no_url.link = ""
    entry_with_url = _make_entry("https://tass.ru/1", "Title")
    mock_feed = MagicMock()
    mock_feed.entries = [entry_no_url, entry_with_url]
    with patch("feedparser.parse", return_value=mock_feed):
        items = fetch_feed("TASS Russian", "https://tass.ru/rss", "Russian", "state_media")
    assert len(items) == 1


def test_fetch_feed_handles_feedparser_exception():
    with patch("feedparser.parse", side_effect=Exception("network error")):
        items = fetch_feed("TASS Russian", "https://tass.ru/rss", "Russian", "state_media")
    assert items == []


def test_fetch_feed_respects_max_items():
    mock_feed = MagicMock()
    mock_feed.entries = [_make_entry(f"https://tass.ru/{i}", f"Title {i}") for i in range(30)]
    with patch("feedparser.parse", return_value=mock_feed):
        items = fetch_feed("TASS Russian", "https://tass.ru/rss", "Russian", "state_media", max_items=5)
    assert len(items) == 5


def test_fetch_feed_includes_url_hash():
    mock_feed = MagicMock()
    mock_feed.entries = [_make_entry("https://tass.ru/1", "Title")]
    with patch("feedparser.parse", return_value=mock_feed):
        items = fetch_feed("TASS Russian", "https://tass.ru/rss", "Russian", "state_media")
    assert "url_hash" in items[0]
    assert len(items[0]["url_hash"]) == 32


# ── fetch_all_feeds ───────────────────────────────────────────────────────────

def test_fetch_all_feeds_deduplicates_across_sources():
    mock_feed = MagicMock()
    mock_feed.entries = [_make_entry("https://shared.url/1", "Title")]
    sources = [
        ("Source A", "https://a.com/rss", "Russian", "adversary"),
        ("Source B", "https://b.com/rss", "Russian", "adversary"),
    ]
    with patch("feedparser.parse", return_value=mock_feed):
        items = fetch_all_feeds(sources)
    # Same URL from two sources — should appear only once
    assert len(items) == 1


def test_fetch_all_feeds_empty_sources():
    items = fetch_all_feeds([])
    assert items == []
