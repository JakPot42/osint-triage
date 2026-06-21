"""SQLite persistence for the OSINT triage queue.

Single table: items — stores raw article fields + extraction results in-row.
Status lifecycle: pending -> done | error
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


_CREATE_ITEMS = """
CREATE TABLE IF NOT EXISTS items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name     TEXT    NOT NULL,
    language        TEXT    NOT NULL,
    outlet          TEXT    NOT NULL,
    url             TEXT    UNIQUE NOT NULL,
    url_hash        TEXT    NOT NULL,
    title_original  TEXT,
    body_original   TEXT,
    published_at    TEXT,
    ingested_at     TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'pending',
    language_detected TEXT,
    translation     TEXT,
    claims_json     TEXT,
    entities_json   TEXT,
    topic           TEXT,
    topic_tags_json TEXT,
    sensitivity     TEXT,
    priority_score  INTEGER,
    priority_tier   TEXT,
    matched_areas_json TEXT,
    extracted_at    TEXT
);
"""


class TriageDB:
    def __init__(self, db_path: str = ":memory:") -> None:
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(_CREATE_ITEMS)
        self._conn.commit()

    # ── ingestion ─────────────────────────────────────────────────────────────

    def add_item(self, item: dict) -> int | None:
        """Insert a raw item. Returns inserted row id, or None if URL already exists."""
        if self.url_exists(item["url"]):
            return None
        now = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            """INSERT INTO items
               (source_name, language, outlet, url, url_hash, title_original,
                body_original, published_at, ingested_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item["source_name"], item["language"], item["outlet"],
                item["url"], item["url_hash"],
                item.get("title_original", ""), item.get("body_original", ""),
                item.get("published_at", now), now,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def url_exists(self, url: str) -> bool:
        row = self._conn.execute("SELECT 1 FROM items WHERE url = ?", (url,)).fetchone()
        return row is not None

    # ── extraction ────────────────────────────────────────────────────────────

    def mark_extracted(self, item_id: int, extraction: dict, score: int,
                       tier: str, matched_areas: list[str]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        entities = extraction.get("entities", {})
        self._conn.execute(
            """UPDATE items SET
               status = 'done',
               language_detected = ?,
               translation       = ?,
               claims_json       = ?,
               entities_json     = ?,
               topic             = ?,
               topic_tags_json   = ?,
               sensitivity       = ?,
               priority_score    = ?,
               priority_tier     = ?,
               matched_areas_json = ?,
               extracted_at      = ?
               WHERE id = ?""",
            (
                extraction.get("language"),
                extraction.get("translation"),
                json.dumps(extraction.get("claims", [])),
                json.dumps(entities),
                extraction.get("topic"),
                json.dumps(extraction.get("topic_tags", [])),
                extraction.get("sensitivity"),
                score, tier,
                json.dumps(matched_areas),
                now, item_id,
            ),
        )
        self._conn.commit()

    def mark_error(self, item_id: int) -> None:
        self._conn.execute(
            "UPDATE items SET status = 'error' WHERE id = ?", (item_id,)
        )
        self._conn.commit()

    # ── queries ───────────────────────────────────────────────────────────────

    def get_pending_items(self, limit: int | None = None) -> list[dict]:
        q = "SELECT * FROM items WHERE status = 'pending' ORDER BY ingested_at ASC"
        if limit:
            q += f" LIMIT {int(limit)}"
        return [dict(r) for r in self._conn.execute(q).fetchall()]

    def get_triaged_items(self, tier: str | None = None, limit: int | None = None) -> list[dict]:
        if tier:
            q = "SELECT * FROM items WHERE status = 'done' AND priority_tier = ? ORDER BY priority_score DESC"
            rows = self._conn.execute(q, (tier,)).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM items WHERE status = 'done' ORDER BY priority_score DESC"
            ).fetchall()
        result = [dict(r) for r in rows]
        if limit:
            result = result[:limit]
        return result

    def get_stats(self) -> dict:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) as n FROM items GROUP BY status"
        ).fetchall()
        stats = {r["status"]: r["n"] for r in rows}
        tier_rows = self._conn.execute(
            "SELECT priority_tier, COUNT(*) as n FROM items WHERE status='done' GROUP BY priority_tier"
        ).fetchall()
        stats["tiers"] = {r["priority_tier"]: r["n"] for r in tier_rows}
        return stats

    # ── demo seeding ──────────────────────────────────────────────────────────

    def seed_demo(self, seeds: list[dict]) -> None:
        """Insert pre-baked demo items with pre-populated extractions."""
        import hashlib
        from osint_triage.scorer import score_item, score_to_tier

        for seed in seeds:
            url = seed["url"]
            url_hash = hashlib.md5(url.encode()).hexdigest()
            now = datetime.now(timezone.utc).isoformat()

            if self.url_exists(url):
                continue

            extraction = seed["extraction"]
            score, matched = score_item(extraction)
            tier = score_to_tier(score)
            entities = extraction.get("entities", {})

            self._conn.execute(
                """INSERT INTO items
                   (source_name, language, outlet, url, url_hash, title_original,
                    body_original, published_at, ingested_at, status,
                    language_detected, translation, claims_json, entities_json,
                    topic, topic_tags_json, sensitivity,
                    priority_score, priority_tier, matched_areas_json, extracted_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    seed["source_name"], seed["language"], seed["outlet"],
                    url, url_hash,
                    seed.get("title_original", ""), seed.get("body_original", ""),
                    now, now, "done",
                    extraction.get("language"),
                    extraction.get("translation"),
                    json.dumps(extraction.get("claims", [])),
                    json.dumps(entities),
                    extraction.get("topic"),
                    json.dumps(extraction.get("topic_tags", [])),
                    extraction.get("sensitivity"),
                    score, tier,
                    json.dumps(matched),
                    now,
                ),
            )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
