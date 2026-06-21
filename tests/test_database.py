"""Tests for database.py."""
import json

import pytest

from osint_triage.database import TriageDB


@pytest.fixture
def db():
    d = TriageDB(":memory:")
    yield d
    d.close()


def _item(url="https://tass.ru/1", source="TASS Russian", lang="Russian"):
    import hashlib
    return {
        "source_name": source,
        "language": lang,
        "outlet": "state_media",
        "url": url,
        "url_hash": hashlib.md5(url.encode()).hexdigest(),
        "title_original": "Заголовок",
        "body_original": "Текст статьи",
        "published_at": "2026-06-01T12:00:00+00:00",
    }


def _extraction():
    return {
        "language": "Russian",
        "translation": "Russia tested an ICBM at Plesetsk.",
        "claims": ["Sarmat ICBM tested"],
        "entities": {"persons": [], "organizations": ["MoD"], "locations": ["Plesetsk"]},
        "topic": "Nuclear/WMD",
        "topic_tags": ["nuclear", "icbm"],
        "sensitivity": "CRITICAL",
    }


# ── add_item ──────────────────────────────────────────────────────────────────

def test_add_item_returns_id(db):
    row_id = db.add_item(_item())
    assert isinstance(row_id, int)
    assert row_id > 0


def test_add_item_duplicate_url_returns_none(db):
    db.add_item(_item())
    result = db.add_item(_item())
    assert result is None


def test_url_exists_true(db):
    db.add_item(_item())
    assert db.url_exists("https://tass.ru/1") is True


def test_url_exists_false(db):
    assert db.url_exists("https://tass.ru/999") is False


# ── mark_extracted ────────────────────────────────────────────────────────────

def test_mark_extracted_updates_status(db):
    item_id = db.add_item(_item())
    db.mark_extracted(item_id, _extraction(), score=85, tier="CRITICAL", matched_areas=["Nuclear/WMD"])
    items = db.get_triaged_items()
    assert len(items) == 1
    assert items[0]["status"] == "done"
    assert items[0]["priority_score"] == 85
    assert items[0]["priority_tier"] == "CRITICAL"


def test_mark_extracted_stores_claims(db):
    item_id = db.add_item(_item())
    db.mark_extracted(item_id, _extraction(), score=85, tier="CRITICAL", matched_areas=["Nuclear/WMD"])
    items = db.get_triaged_items()
    claims = json.loads(items[0]["claims_json"])
    assert "Sarmat ICBM tested" in claims


def test_mark_extracted_stores_entities(db):
    item_id = db.add_item(_item())
    db.mark_extracted(item_id, _extraction(), score=85, tier="CRITICAL", matched_areas=["Nuclear/WMD"])
    items = db.get_triaged_items()
    entities = json.loads(items[0]["entities_json"])
    assert "Plesetsk" in entities["locations"]


# ── mark_error ────────────────────────────────────────────────────────────────

def test_mark_error_updates_status(db):
    item_id = db.add_item(_item())
    db.mark_error(item_id)
    pending = db.get_pending_items()
    assert len(pending) == 0


# ── get_pending_items ─────────────────────────────────────────────────────────

def test_get_pending_items_returns_new_items(db):
    db.add_item(_item("https://tass.ru/1"))
    db.add_item(_item("https://tass.ru/2"))
    pending = db.get_pending_items()
    assert len(pending) == 2


def test_get_pending_items_limit(db):
    for i in range(5):
        db.add_item(_item(f"https://tass.ru/{i}"))
    pending = db.get_pending_items(limit=3)
    assert len(pending) == 3


def test_get_pending_excludes_done(db):
    item_id = db.add_item(_item("https://tass.ru/1"))
    db.mark_extracted(item_id, _extraction(), 85, "CRITICAL", ["Nuclear/WMD"])
    db.add_item(_item("https://tass.ru/2"))
    pending = db.get_pending_items()
    assert len(pending) == 1


# ── get_triaged_items ─────────────────────────────────────────────────────────

def test_get_triaged_items_sorted_by_score(db):
    for url, score, tier in [
        ("https://a.com/1", 30, "MEDIUM"),
        ("https://a.com/2", 90, "CRITICAL"),
        ("https://a.com/3", 55, "HIGH"),
    ]:
        item_id = db.add_item(_item(url))
        db.mark_extracted(item_id, _extraction(), score, tier, [])
    items = db.get_triaged_items()
    scores = [i["priority_score"] for i in items]
    assert scores == sorted(scores, reverse=True)


def test_get_triaged_items_filter_by_tier(db):
    for url, score, tier in [
        ("https://a.com/1", 90, "CRITICAL"),
        ("https://a.com/2", 55, "HIGH"),
    ]:
        item_id = db.add_item(_item(url))
        db.mark_extracted(item_id, _extraction(), score, tier, [])
    items = db.get_triaged_items(tier="CRITICAL")
    assert all(i["priority_tier"] == "CRITICAL" for i in items)
    assert len(items) == 1


# ── get_stats ─────────────────────────────────────────────────────────────────

def test_get_stats_counts(db):
    item_id = db.add_item(_item("https://a.com/1"))
    db.add_item(_item("https://a.com/2"))
    db.mark_extracted(item_id, _extraction(), 85, "CRITICAL", [])
    stats = db.get_stats()
    assert stats.get("pending", 0) == 1
    assert stats.get("done", 0) == 1


def test_get_stats_empty_db(db):
    stats = db.get_stats()
    assert stats.get("pending", 0) == 0
    assert stats.get("done", 0) == 0


# ── seed_demo ─────────────────────────────────────────────────────────────────

def test_seed_demo_inserts_items(db):
    from osint_triage.config import DEMO_SEEDS
    db.seed_demo(DEMO_SEEDS)
    items = db.get_triaged_items()
    assert len(items) == len(DEMO_SEEDS)


def test_seed_demo_idempotent(db):
    from osint_triage.config import DEMO_SEEDS
    db.seed_demo(DEMO_SEEDS)
    db.seed_demo(DEMO_SEEDS)
    items = db.get_triaged_items()
    assert len(items) == len(DEMO_SEEDS)


def test_seed_demo_scores_correctly(db):
    from osint_triage.config import DEMO_SEEDS
    db.seed_demo(DEMO_SEEDS)
    items = db.get_triaged_items()
    # Items with nuclear/ICBM content should be CRITICAL
    nuclear_items = [i for i in items if "Nuclear" in (i.get("topic") or "")]
    assert any(i["priority_tier"] == "CRITICAL" for i in nuclear_items)
