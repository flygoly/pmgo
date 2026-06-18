# risk-radar

Aggregate **open / watching** risks, **blocked** tasks, and **stale blockers (>24h)** from `memory/pmgo.db`.

## Responsibilities

- Query `risks` where `status IN ('open','watching')`, ordered by severity then `created_at`.
- Query `tasks` where `status = 'blocked'` for the same `project_id`.
- Flag blocked tasks with `updated_at` older than 24 hours as `tasks_blocked_stale_24h`.
- Return JSON (CLI) or MCP `pmgo_risk_scan` with `summary` counts.

Risk CRUD lives in **project-core** (`risk-list`, `pmgo_risk_create`, …).

## Implementation

- `skills/risk-radar/risk_radar/scan.py` — SQLite queries
- `skills/risk-radar/risk_radar/cli.py` — `report` subcommand
- `scripts/risk-radar.py` — launcher (`npm run risk-radar -- …`)

## CLI

```bash
python3 scripts/risk-radar.py report --project-id <UUID>
# or
npm run risk-radar -- report --project-id <UUID>
```

- `--from-first-project` — first project in DB, or exit 0 if none (used for `risk-radar:smoke` / CI).
- `--db PATH` — override `PMGO_MEMORY_DB` / default `memory/pmgo.db`.

## MCP (OpenClaw & Hermes)

- Scan (read): `pmgo_risk_scan` — policy key `pmgo.risk.scan`. Optional `auto_escalate=true` (+ `confirmed=true`) creates risks for blockers stale >24h.
- CRUD: `pmgo_risk_list`, `pmgo_risk_create`, `pmgo_risk_update` — policy keys `project_core.risk.*`

Stale-blocker escalation is implemented in `risk_radar/escalate.py` (evidence marker `pmgo_task_id:{uuid}`).
