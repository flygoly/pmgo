# canvas-data

JSON snapshots + Live Canvas HTML artifacts (Gantt + burndown).

## CLI

```bash
npm run canvas -- gantt --project-id <UUID>
npm run canvas -- burndown --project-id <UUID>
npm run canvas -- snapshot --project-id <UUID>

# Render HTML + data.json → reports/canvas/pmgo/
npm run canvas:render -- --project-id <UUID>
npm run canvas:render -- --from-first-project
```

Uses `PMGO_DEFAULT_PROJECT_ID` when `--project-id` / `--from-first-project` is set.

## MCP

| Tool | Policy |
| --- | --- |
| `pmgo_canvas_gantt` | `pmgo.canvas.read` |
| `pmgo_canvas_burndown` | `pmgo.canvas.read` |
| `pmgo_canvas_snapshot` | `pmgo.canvas.read` |
| `pmgo_canvas_render` | `pmgo.canvas.read` |

`pmgo_canvas_render` returns `out_dir` / file paths plus `runtime_notes`:

- **OpenClaw:** set `canvasHost.root` to `out_dir`, then present `/__openclaw__/canvas/index.html`
- **Hermes:** no canvas host — open `index.html` locally if useful, otherwise use Markdown reports (`pmgo_daily_report` / `pmgo_weekly_report`)

## Schema

- `pmgo.canvas.gantt/v1` — milestones + tasks with `due_at` / status
- `pmgo.canvas.burndown/v1` — UTC-week ideal vs actual remaining points
- `pmgo.canvas.snapshot/v1` — both payloads together

Template: `runtimes/openclaw/canvas/pmgo/index.html`  
See [docs/LIVE_CANVAS.md](../../docs/LIVE_CANVAS.md).
