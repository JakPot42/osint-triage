# Foreign-Language OSINT Triage

> **INSTITUTIONAL/MEDIA LEVEL ONLY** — public foreign-language news sources. Not surveillance of individuals.

A CLI tool that ingests native-language adversary/state media, translates and extracts key claims via Claude Haiku, then scores each item deterministically against analyst-defined interest areas to produce a prioritized triage queue.

Addresses a documented IC capability gap: human linguist time is finite. This tool flags what's worth a linguist's attention before they read it.

---

## What it does

1. **Ingests** native-language RSS feeds from adversary/state media (Russian, Chinese, Arabic, Spanish, Persian)
2. **Extracts** via Claude Haiku: English translation, key claims, named entities, topic classification, urgency signals
3. **Scores** deterministically — keyword matching against analyst-defined interest areas (no Claude for scoring, fully auditable)
4. **Outputs** a prioritized triage queue with original-language source links preserved for linguist verification

---

## Sources

| Source | Language | Type |
|---|---|---|
| TASS | Russian | state_media |
| RT Russian | Russian | adversary |
| Sputnik Russian | Russian | adversary |
| Global Times CN | Chinese | state_media |
| Xinhua | Chinese | state_media |
| RT Arabic | Arabic | adversary |
| Sputnik Arabic | Arabic | adversary |
| Sputnik Spanish | Spanish | adversary |
| HispanTV | Spanish | adversary |
| IRNA Persian | Persian | state_media |

---

## Priority tiers

| Tier | Score | Action |
|---|---|---|
| CRITICAL | ≥75 | Pass immediately to senior analyst |
| HIGH | ≥50 | Review within 2 hours |
| MEDIUM | ≥25 | Review within shift |
| LOW | <25 | Batch review end of day |

---

## Quick start

```bash
# No API key needed
python main.py demo

# List configured sources
python main.py sources

# Ingest live feeds (no API key)
python main.py ingest

# Extract + score with Claude (requires ANTHROPIC_API_KEY)
python main.py triage

# Display triage queue
python main.py report
python main.py report --tier CRITICAL
```

Copy `.env.example` to `.env` and add your key:
```
ANTHROPIC_API_KEY=your-key-here
```

---

## Install

```bash
pip install -r requirements.txt
```

---

## Tests

```bash
python -m pytest tests/ -v
```

---

## Architecture

```
osint_triage/
├── config.py       Sources, interest areas, priority tiers, demo seed data
├── feed_client.py  RSS ingestion (feedparser, URL dedup)
├── extractor.py    Claude Haiku: translate + extract claims/entities/topic
├── scorer.py       Deterministic keyword/topic scoring (no Claude)
├── database.py     SQLite triage queue
└── reporter.py     Rich table output
```

**Scoring algorithm:** For each interest area, count keyword hits in the English translation + topic tags. Multiply hits (capped at 3) by area weight. Apply 25% multi-area bonus when 2+ areas match. Cap at 100.

**Analyst interest areas:** Nuclear/WMD (weight 25), Technology Transfer (20), Cyber Operations (18), Taiwan/South China Sea (20), Military Operations (15), Ukraine/NATO (15), Middle East (15), Sanctions/Trade (10), Diplomacy (8).

---

## Portfolio context

P50 is part of the Intelligence Analysis cluster alongside:
- **P37 SENTINEL** — English-language adversary media monitoring
- **P41 redteam-eval** — adversarial LLM evaluation
- **P45 AnalystDesk** — structured analytic workflow

GitHub: [JakPot42](https://github.com/JakPot42)
