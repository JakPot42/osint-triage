"""Tests for main.py CLI commands."""
import pytest
from click.testing import CliRunner

from main import cli


@pytest.fixture
def runner():
    return CliRunner()


# ── demo ──────────────────────────────────────────────────────────────────────

def test_demo_exits_zero(runner):
    result = runner.invoke(cli, ["demo"])
    assert result.exit_code == 0, result.output


def test_demo_shows_framing_note(runner):
    result = runner.invoke(cli, ["demo"])
    assert "INSTITUTIONAL" in result.output or "media level" in result.output.lower()


def test_demo_shows_triage_queue(runner):
    result = runner.invoke(cli, ["demo"])
    assert "CRITICAL" in result.output or "HIGH" in result.output or "Triage Queue" in result.output


def test_demo_shows_scoring_explanation(runner):
    result = runner.invoke(cli, ["demo"])
    assert "score" in result.output.lower() or "Score" in result.output


# ── sources ───────────────────────────────────────────────────────────────────

def test_sources_exits_zero(runner):
    result = runner.invoke(cli, ["sources"])
    assert result.exit_code == 0, result.output


def test_sources_lists_russian(runner):
    result = runner.invoke(cli, ["sources"])
    assert "Russian" in result.output


def test_sources_lists_chinese(runner):
    result = runner.invoke(cli, ["sources"])
    assert "Chinese" in result.output


def test_sources_lists_arabic(runner):
    result = runner.invoke(cli, ["sources"])
    assert "Arabic" in result.output


# ── report (empty DB) ─────────────────────────────────────────────────────────

def test_report_empty_db(runner, tmp_path):
    db_path = str(tmp_path / "test.db")
    result = runner.invoke(cli, ["report", "--db", db_path])
    assert result.exit_code == 0
    assert "No triaged items" in result.output or "pending" in result.output or "Total" in result.output


def test_report_with_tier_filter(runner, tmp_path):
    db_path = str(tmp_path / "test.db")
    result = runner.invoke(cli, ["report", "--db", db_path, "--tier", "CRITICAL"])
    assert result.exit_code == 0


# ── triage (no API key) ───────────────────────────────────────────────────────

def test_triage_without_api_key_exits_nonzero(runner, tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    db_path = str(tmp_path / "test.db")
    result = runner.invoke(cli, ["triage", "--db", db_path])
    assert result.exit_code != 0


# ── ingest (mocked feedparser) ────────────────────────────────────────────────

def test_ingest_with_empty_feeds(runner, tmp_path):
    from unittest.mock import MagicMock, patch
    db_path = str(tmp_path / "test.db")
    mock_feed = MagicMock()
    mock_feed.entries = []
    with patch("feedparser.parse", return_value=mock_feed):
        result = runner.invoke(cli, ["ingest", "--db", db_path])
    assert result.exit_code == 0
    assert "Added:" in result.output


def test_ingest_adds_items(runner, tmp_path):
    from unittest.mock import MagicMock, patch
    import hashlib

    db_path = str(tmp_path / "test.db")
    entry = MagicMock()
    entry.link = "https://tass.ru/test/1"
    entry.title = "Тестовый заголовок"
    entry.summary = "Тестовый текст"
    entry.content = []
    entry.published_parsed = (2026, 6, 1, 12, 0, 0, 0, 0, 0)

    mock_feed = MagicMock()
    mock_feed.entries = [entry]
    with patch("feedparser.parse", return_value=mock_feed):
        result = runner.invoke(cli, ["ingest", "--db", db_path])
    assert result.exit_code == 0
    assert "Added:" in result.output
