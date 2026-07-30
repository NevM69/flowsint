# Centrale — Dashboard

Unified read-only view across the whole lab: OSINT investigations
(flowsint-api), forensic cases (IPED/autopsy), pentest lab reports
(Awesome-Pentest), and the blue-team pivot queue (pcybox-orbis). Nothing
here talks to a hosted service — every source is either a local file this
machine already produces, or your own flowsint-api instance.

Each of the four tabs is independent and optional: unset its config and the
tab just shows "non configuré" instead of erroring. There's no requirement
to run all four repos to get value from this.

## Data sources

| Tab | Reads from | Written by |
|---|---|---|
| OSINT | `flowsint-api`'s `/auth/token` + `/investigations` | flowsint-api itself |
| Forensique | `<cases_dir>/*/chain_of_custody.log` | `IPED/docker/acquire_and_hash.sh`, `autopsy/docker/acquire_and_hash.sh` |
| Pentest | `<reports_dir>/<timestamp>/report.md` | `Awesome-Pentest/lab/run_playbook.sh` |
| Blue team | a JSONL pivot queue | `pcybox-orbis/blueteam/export_pivots.py` |

## Setup

```sh
cd centrale-dashboard
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in whichever sources you have running
uvicorn centrale_dashboard.main:app --reload
```

Open `http://127.0.0.1:8000`. The page polls all four `/api/*` endpoints
every 30s — no websocket, no build step, just static HTML/CSS/JS served
alongside the API.

## Tests

```sh
pip install -r requirements.txt httpx pytest
pytest tests/ -v
```

31 tests: parsing logic for all four sources (custody-log status
detection, report.md step extraction, pivot-queue dedup/limits,
investigation summarization) plus FastAPI endpoint wiring via
`TestClient`. All were run against a live `uvicorn` instance during
development too (see the commit message for the exact smoke-test output),
not just `TestClient` — this one was build-tested end to end, unlike the
Phase 2/3 Docker images (no daemon available in that environment).

## Notes

- `FORENSICS_SOURCES` takes multiple `Label=/path` pairs (comma-separated)
  since IPED and autopsy each write to their own `cases/` directory — see
  `.env.example`.
- The OSINT tab needs real flowsint-api credentials; it never touches your
  vault secrets or graph data directly, only the two REST endpoints listed
  above.
- This dashboard is read-only by design — it has no write endpoints against
  any of the four systems it displays.
