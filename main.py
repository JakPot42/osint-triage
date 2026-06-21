"""Foreign-Language OSINT Triage CLI.

INSTITUTIONAL/MEDIA LEVEL ONLY — public foreign-language news sources.
Not surveillance of individuals.
"""
from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_dotenv()

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from osint_triage.config import (
    DB_PATH,
    DEMO_SEEDS,
    FOREIGN_SOURCES,
    FRAMING_NOTE,
    MAX_EXTRACT_PER_RUN,
    MAX_ITEMS_PER_FEED,
    TIER_COLORS,
)
from osint_triage.database import TriageDB
from osint_triage.reporter import console, print_stats, print_triage_table

_FRAMING_PANEL = Panel(
    f"[dim]{FRAMING_NOTE}[/dim]",
    border_style="dim",
    title="[dim]P50 — Foreign-Language OSINT Triage[/dim]",
)


@click.group()
def cli() -> None:
    """Foreign-Language OSINT Triage — P50.

    \b
    Ingests native-language adversary/state media, translates via Claude,
    scores deterministically against analyst interest areas.

    \b
    Commands:
      ingest   Fetch foreign-language RSS feeds into the triage DB
      triage   Extract + score pending items using Claude Haiku
      report   Display the prioritized triage queue
      sources  List all configured foreign-language sources
      demo     Self-contained walkthrough with pre-seeded data
    """


# ── sources ───────────────────────────────────────────────────────────────────────

@cli.command()
def sources() -> None:
    """List all configured foreign-language sources."""
    table = Table(title="Configured Foreign-Language Sources", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Language")
    table.add_column("Type")
    table.add_column("URL")

    for name, url, lang, outlet in FOREIGN_SOURCES:
        table.add_row(name, lang, outlet, url)

    console.print(table)
    console.print(f"\n[dim]{FRAMING_NOTE}[/dim]")


# ── ingest ────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--db", "db_path", default=None, help="Override DB path.")
@click.option("--max-per-feed", default=MAX_ITEMS_PER_FEED, show_default=True, type=int,
              help="Max items to fetch per feed.")
def ingest(db_path, max_per_feed) -> None:
    """Fetch foreign-language RSS feeds and store raw items in the triage DB."""
    console.print()
    console.print(_FRAMING_PANEL)

    from osint_triage.feed_client import fetch_all_feeds

    console.print(f"\n[bold]Fetching {len(FOREIGN_SOURCES)} foreign-language feeds...[/bold]")
    items = fetch_all_feeds(FOREIGN_SOURCES, max_items=max_per_feed)
    console.print(f"  Fetched [cyan]{len(items)}[/cyan] items total.")

    db = TriageDB(db_path or DB_PATH)
    added = 0
    skipped = 0
    for item in items:
        result = db.add_item(item)
        if result is not None:
            added += 1
        else:
            skipped += 1

    console.print(f"  Added: [green]{added}[/green] | Skipped (dupes): [dim]{skipped}[/dim]")
    print_stats(db.get_stats())
    db.close()
    console.print("\n[dim]Run `python main.py triage` to extract and score pending items.[/dim]")


# ── triage ────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--db", "db_path", default=None, help="Override DB path.")
@click.option("--limit", default=MAX_EXTRACT_PER_RUN, show_default=True, type=int,
              help="Max items to extract per run.")
def triage(db_path, limit) -> None:
    """Extract and score pending items using Claude Haiku.

    Requires ANTHROPIC_API_KEY.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise click.ClickException(
            "ANTHROPIC_API_KEY not set. Add it to .env or set the environment variable."
        )

    console.print()
    console.print(_FRAMING_PANEL)

    from osint_triage.extractor import extract_item
    from osint_triage.scorer import score_item, score_to_tier

    db = TriageDB(db_path or DB_PATH)
    pending = db.get_pending_items(limit=limit)

    if not pending:
        console.print("[yellow]No pending items. Run `python main.py ingest` first.[/yellow]")
        db.close()
        return

    console.print(f"\n[bold]Extracting {len(pending)} items with Claude Haiku...[/bold]")
    done = error = 0

    for item in pending:
        item_id = item["id"]
        title = item.get("title_original") or ""
        body = item.get("body_original") or ""
        source = item.get("source_name", "")
        lang = item.get("language", "")

        console.print(f"  [{lang}] {source}: {title[:60]}...")
        try:
            extraction = extract_item(title, body)
            score, matched = score_item(extraction)
            tier = score_to_tier(score)
            db.mark_extracted(item_id, extraction, score, tier, matched)
            tier_color = TIER_COLORS.get(tier, "")
            console.print(
                f"    -> [{tier_color}]{tier}[/{tier_color}] score={score} | {extraction.get('topic')} | {lang}"
            )
            done += 1
        except Exception as exc:
            console.print(f"    [red]error: {exc}[/red]")
            db.mark_error(item_id)
            error += 1

    console.print(f"\n  Done: [green]{done}[/green] | Error: [red]{error}[/red]")
    print_stats(db.get_stats())
    db.close()
    console.print("\n[dim]Run `python main.py report` to display the triage queue.[/dim]")


# ── report ────────────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--db", "db_path", default=None, help="Override DB path.")
@click.option("--tier", default=None, type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
              help="Filter by priority tier.")
@click.option("--limit", default=50, show_default=True, type=int, help="Max items to show.")
def report(db_path, tier, limit) -> None:
    """Display the prioritized triage queue."""
    db = TriageDB(db_path or DB_PATH)
    items = db.get_triaged_items(tier=tier, limit=limit)
    stats = db.get_stats()
    db.close()

    console.print()
    console.print(_FRAMING_PANEL)
    console.print()
    print_stats(stats)
    console.print()

    title = "Triage Queue"
    if tier:
        title += f" — {tier} only"
    print_triage_table(items, title=title)


# ── demo ──────────────────────────────────────────────────────────────────────────

@cli.command()
def demo() -> None:
    """Self-contained walkthrough with pre-seeded data — no API key needed.

    Seeds the in-memory DB with 9 example items spanning Russian, Chinese,
    Arabic, and Spanish sources, then displays the full triage queue.
    """
    console.print()
    console.print(Panel(
        "[bold]Foreign-Language OSINT Triage — Demo[/bold]\n"
        "Multilingual adversary media triage using Claude Haiku\n\n"
        f"[dim]{FRAMING_NOTE}[/dim]",
        border_style="blue",
        title="[bold]P50[/bold]",
    ))

    console.print("\n[bold underline]Step 1 — Seed demo article bank[/bold underline]")
    console.print(f"  {len(DEMO_SEEDS)} illustrative articles across Russian, Chinese, Arabic, Spanish")
    console.print("  [dim](Pre-baked extractions — no API key needed for demo)[/dim]")

    db = TriageDB(":memory:")
    db.seed_demo(DEMO_SEEDS)

    stats = db.get_stats()
    print_stats(stats)

    console.print("\n[bold underline]Step 2 — Triage queue (scored by interest area)[/bold underline]")
    items = db.get_triaged_items()
    print_triage_table(items, title="Demo Triage Queue")

    console.print("\n[bold underline]Step 3 — How scoring works[/bold underline]")
    console.print("  Priority score = keyword hits × interest area weight (capped at 100)")
    console.print("  Multi-area match adds 25% bonus")
    console.print("  Tiers: [bold red]CRITICAL[/bold red] ≥75 | [bold yellow]HIGH[/bold yellow] ≥50 | [cyan]MEDIUM[/cyan] ≥25 | [dim]LOW[/dim] <25")

    console.print()
    console.print(Panel(
        "Run [bold]python main.py ingest[/bold] to fetch live foreign-language feeds.\n"
        "Run [bold]python main.py triage[/bold] (needs ANTHROPIC_API_KEY) to extract + score live items.\n"
        "Run [bold]python main.py report[/bold] to display the live triage queue.",
        border_style="green",
        title="[bold]Next steps[/bold]",
    ))

    db.close()


if __name__ == "__main__":
    cli()
