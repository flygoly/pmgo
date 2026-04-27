# risk-radar

Aggregate **open / watching** rows from `memory/pmgo.db` `risks` and **blocked** tasks for visibility and standups.

## Responsibilities

- Query `risks` where `status IN ('open','watching')`, ordered by severity then `created_at`.
- Query `tasks` where `status = 'blocked'` for the same `project_id`.
- Return JSON (CLI) or MCP `pmgo_risk_scan` with `summary` counts.

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

## OpenClaw

Policy key: `pmgo.risk.scan` (read). Tool: `pmgo_risk_scan`.

## Future work

- Optional Markdown section for daily/weekly templates; trend from `risk_events` if populated.
