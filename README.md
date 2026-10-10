# Terps Football · Maryland Wall

A **multi-screen Terps wall** for Maryland football (2026), built for Boyd (UMD alum) by TokenMax. Maryland red/gold dark UI, next-game kickoff in ET, season notes from on-disk ESPN cache only — **never invent scores**.

## What's new — Sat Oct 10 afternoon remaster
- **Multi-screen wall:** Wall · Results · Bowl Watch · Big Ten · Schedule · Leaders · Season Notes (sticky screen nav).
- **Night wall aesthetic:** deep red void, gold trim, Maryland flag band (replaces single long scroll page).
- **Season Notes screen:** record/streak/next/bowl/FCS + disclosed data quirks (standings seed vs standingSummary; tackles feed vs box sums) and labelled estimates — all from `data/tracker.json` + `data/season_notes.json`.
- **Ship pattern:** `export_static.py` → `dist/terps-football-snapshot.html`; `screenshot.sh` → `screenshots/00-best-home.png`; `run.sh` + stdlib server on **127.0.0.1:4279**.
- Port moved from 4272 → **4279** (127.0.0.1 only).

## Open it
- Live: http://127.0.0.1:4279 (`./run.sh start`)
- Offline: `dist/terps-football-snapshot.html` (also `dist/terps-football-2026.html` / `dist/index.html`)
- Best screenshot: `screenshots/00-best-home.png` (also overview / full / mobile / live)

## Headline (ESPN cache fetched Oct 7, 2026 ET)
| | |
|---|---|
| Record | 2–3 overall, 0–2 Big Ten · ESPN seed 16/18 · streak L3 |
| Next | Sat Oct 10, **4:15 PM ET** @ Ohio State (4–1) · BTN · DraftKings OSU −34.5 · ESPN MD win 1.6% |
| Bowl | 2 countable wins (1 FCS win counts) · need 4 of 7 left · P(bowl) **5.4%** Estimate · expected ≈ 3.8 wins |

## Data (real only)
`fetch.py` caches ESPN responses in `data/raw/`; `build.py` → `data/tracker.json`; season notes regenerated from tracker. Manifest records URL, fetch time, HTTP status, bytes, sha256. Estimates (bowl probability, record-model bars) are labelled **Estimate**.

## Commands
```
./run.sh start|stop|restart|status
./run.sh ship      # export_static + restart + screenshots + smoke
./run.sh build     # build.py + export_static + screenshot.sh
./run.sh test      # python3 tests/smoke_test.py
./run.sh fetch     # re-pull ESPN then build (optional; remaster used on-disk data)
```

## Privacy
Public ESPN JSON only. No accounts, no keys. Server binds 127.0.0.1. Betting lines informational. Not affiliated with the Big Ten, ESPN, any bookmaker, or the University of Maryland.


---
## Repo notes
- **Built:** Oct 7, 2026, by TokenMax (Boyd's Grok Bot) on the Grok Bot box.
- **Run:** `./run.sh` (then open the localhost URL it prints).
- Imported from `/workspace/tokenmax/terps-football` on Oct 23, 2026. node_modules, virtualenvs, logs and files over 20 MB were left out.
- Personal details (emails, phone numbers, home street address) were replaced with `[redacted-…]` placeholders.
