# canvas-data

Read-only JSON snapshots for **OpenClaw Live Canvas** (Gantt + burndown).

## CLI

```bash
npm run canvas -- gantt --project-id <UUID>
npm run canvas -- burndown --project-id <UUID>
npm run canvas -- snapshot --project-id <UUID>
```

Uses `PMGO_DEFAULT_PROJECT_ID` when `--project-id` / `--from-first-project` is set.

## MCP

| Tool | Policy |
| --- | --- |
| `pmgo_canvas_gantt` | `pmgo.canvas.read` |
| `pmgo_canvas_burndown` | `pmgo.canvas.read` |
| `pmgo_canvas_snapshot` | `pmgo.canvas.read` |

## Schema

- `pmgo.canvas.gantt/v1` — milestones + tasks with `due_at` / status
- `pmgo.canvas.burndown/v1` — UTC-week ideal vs actual remaining points
- `pmgo.canvas.snapshot/v1` — both payloads together

See [docs/LIVE_CANVAS.md](../../docs/LIVE_CANVAS.md).
