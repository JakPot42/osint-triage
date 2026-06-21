"""RSS feed ingestion for foreign-language OSINT sources.

Mirrors SENTINEL's ingestor pattern: feedparser + URL dedup via hash.
Does NOT write to DB — returns raw item dicts for the caller to persist.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone


def _clean_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def fetch_feed(source_name: str, url: str, language: str, outlet: str,
               max_items: int = 25) -> list[dict]:
    """Fetch a single RSS feed. Returns a list of raw item dicts.

    Each item: source_name, language, outlet, url, url_hash,
                title_original, body_original, published_at
    """
    try:
        import feedparser
    except ImportError as exc:
        raise ImportError("feedparser not installed — run: pip install feedparser") from exc

    try:
        feed = feedparser.parse(url)
    except Exception:
        return []

    items = []
    seen_hashes: set[str] = set()

    for entry in feed.entries[:max_items]:
        entry_url = getattr(entry, "link", "")
        if not entry_url:
            continue
        h = _url_hash(entry_url)
        if h in seen_hashes:
            continue
        seen_hashes.add(h)

        title = _clean_html(getattr(entry, "title", "") or "")
        summary = _clean_html(getattr(entry, "summary", "") or "")
        content_val = ""
        if hasattr(entry, "content") and entry.content:
            content_val = _clean_html(entry.content[0].get("value", "") or "")
        body = content_val or summary

        pub_struct = getattr(entry, "published_parsed", None)
        if pub_struct:
            try:
                published_at = datetime(*pub_struct[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                published_at = datetime.now(timezone.utc).isoformat()
        else:
            published_at = datetime.now(timezone.utc).isoformat()

        items.append({
            "source_name": source_name,
            "language": language,
            "outlet": outlet,
            "url": entry_url,
            "url_hash": h,
            "title_original": title,
            "body_original": body,
            "published_at": published_at,
        })

    return items


def fetch_all_feeds(sources: list[tuple], max_items: int = 25) -> list[dict]:
    """Fetch all configured sources. sources is a list of (name, url, language, outlet) tuples."""
    all_items: list[dict] = []
    seen_hashes: set[str] = set()

    for source_name, url, language, outlet in sources:
        items = fetch_feed(source_name, url, language, outlet, max_items)
        for item in items:
            if item["url_hash"] not in seen_hashes:
                seen_hashes.add(item["url_hash"])
                all_items.append(item)

    return all_items
