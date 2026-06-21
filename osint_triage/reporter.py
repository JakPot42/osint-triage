"""Rich-formatted triage queue output."""
from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from osint_triage.config import TIER_COLORS

console = Console(legacy_windows=False)


def _truncate(s: str | None, n: int) -> str:
    if not s:
        return ""
    return s if len(s) <= n else s[: n - 1] + "…"


def _tier_markup(tier: str, score: int) -> str:
    style = TIER_COLORS.get(tier, "")
    if style:
        return f"[{style}]{tier}[/{style}]\n[dim]{score}[/dim]"
    return f"{tier}\n[dim]{score}[/dim]"


def print_triage_table(items: list[dict], title: str = "Triage Queue") -> None:
    """Print a Rich table of triaged items sorted by priority_score descending."""
    if not items:
        console.print("[yellow]No triaged items to display.[/yellow]")
        return

    table = Table(title=title, show_lines=True, expand=True)
    table.add_column("Tier/Score", min_width=10, no_wrap=True)
    table.add_column("Source / Lang", min_width=14)
    table.add_column("Original Title", min_width=22)
    table.add_column("Translation + Claim", min_width=30, ratio=3)
    table.add_column("Topic", min_width=15)
    table.add_column("URL", min_width=18, no_wrap=True)

    for item in items:
        tier = item.get("priority_tier") or "LOW"
        score = item.get("priority_score") or 0
        source_lang = f"{item.get('source_name','')}\n[dim]{item.get('language','')}[/dim]"
        original = _truncate(item.get("title_original"), 50)
        translation = _truncate(item.get("translation"), 100)
        topic = item.get("topic") or ""

        claims_raw = item.get("claims_json") or "[]"
        try:
            claims = json.loads(claims_raw)
        except Exception:
            claims = []
        if claims:
            translation += f"\n[dim]• {_truncate(claims[0], 80)}[/dim]"

        table.add_row(
            _tier_markup(tier, score),
            source_lang,
            original,
            translation,
            topic,
            _truncate(item.get("url"), 40),
        )

    console.print(table)


def print_stats(stats: dict) -> None:
    """Print a summary stats panel."""
    total = sum(v for k, v in stats.items() if k != "tiers")
    tiers = stats.get("tiers", {})
    console.print(
        f"  Total items: [bold]{total}[/bold] | "
        f"Pending: [cyan]{stats.get('pending', 0)}[/cyan] | "
        f"Done: [green]{stats.get('done', 0)}[/green] | "
        f"Error: [red]{stats.get('error', 0)}[/red]"
    )
    if tiers:
        parts = []
        for t in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            n = tiers.get(t, 0)
            color = TIER_COLORS.get(t, "")
            parts.append(f"[{color}]{t}: {n}[/{color}]" if color else f"{t}: {n}")
        console.print("  Tiers: " + " | ".join(parts))
