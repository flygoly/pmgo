# OpenClaw Live Canvas (planned)

M3 visualization surface for pmgo. **OpenClaw-only** — Hermes users keep Markdown reports.

## Goals

- **Gantt:** milestones + task `due_at` / status from SQLite
- **Burndown:** done vs remaining tasks in the current UTC week (same bounds as weekly report)

## Data source

Read-only MCP / store queries:

- `pmgo_milestone_list`
- `pmgo_task_list`
- Optional: `pmgo_weekly_report` aggregates for narrative

No separate analytics DB.

## Delivery sketch

1. Agent (or cron) fetches JSON via MCP.
2. OpenClaw Live Canvas renders charts from a small JSON schema (to be frozen at M3).
3. Canvas updates are announce-only; writes still go through policy-gated MCP tools.

## Status

Specification only. Track progress in [ROADMAP.md](./ROADMAP.md). Until shipped, use `npm run weekly-report` / Telegram announce.
