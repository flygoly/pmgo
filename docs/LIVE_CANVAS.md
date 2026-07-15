# OpenClaw Live Canvas

M3 visualization surface for pmgo. **OpenClaw-only** — Hermes users keep Markdown reports.

## Goals

- **Gantt:** milestones + task `due_at` / status from SQLite
- **Burndown:** done vs remaining tasks in the current UTC week (same bounds as weekly report)

## Data source (shipped)

Read-only exports — no separate analytics DB:

```bash
npm run canvas -- gantt --project-id <UUID>
npm run canvas -- burndown --from-first-project
npm run canvas -- snapshot --project-id <UUID>
```

MCP tools (policy `pmgo.canvas.read`):

- `pmgo_canvas_gantt`
- `pmgo_canvas_burndown`
- `pmgo_canvas_snapshot`

Schemas: `pmgo.canvas.gantt/v1`, `pmgo.canvas.burndown/v1`, `pmgo.canvas.snapshot/v1`  
Implementation: `skills/canvas-data/`.

## Delivery sketch

1. Agent (or cron) fetches JSON via MCP / CLI.
2. OpenClaw Live Canvas renders charts from the JSON schema above.
3. Canvas updates are announce-only; writes still go through policy-gated MCP tools.

## Status

**Data export shipped.** Visual rendering remains OpenClaw Canvas UI work. Until a Canvas template is published, paste `snapshot` JSON into any charting surface or keep using Markdown weekly reports.
