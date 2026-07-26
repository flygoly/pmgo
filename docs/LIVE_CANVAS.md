# OpenClaw Live Canvas

M3 visualization surface for pmgo. **OpenClaw-only** — Hermes users keep Markdown reports.

## Goals

- **Gantt:** milestones + task `due_at` / status from SQLite
- **Burndown:** done vs remaining tasks in the current UTC week (same bounds as weekly report)

## Data source

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
- `pmgo_canvas_render` — write HTML + `data.json` under `reports/canvas/pmgo` (returns `runtime_notes` for OpenClaw vs Hermes)

Schemas: `pmgo.canvas.gantt/v1`, `pmgo.canvas.burndown/v1`, `pmgo.canvas.snapshot/v1`  
Implementation: `skills/canvas-data/`.

## Render template (shipped)

Self-contained HTML lives at `runtimes/openclaw/canvas/pmgo/index.html`.

```bash
# Build presentable files (default out: reports/canvas/pmgo/)
npm run canvas:render -- --project-id <UUID>
# or
npm run canvas:render -- --from-first-project
```

Output:

- `index.html` — template with snapshot inlined as `window.__PMGO_DATA__`
- `data.json` — same snapshot for fetch()/live-reload

Point OpenClaw `canvasHost.root` at that directory (or copy its contents into your canvas root):

```json
{
  "canvasHost": {
    "enabled": true,
    "port": 18793,
    "root": "/absolute/path/to/pmgo/reports/canvas/pmgo",
    "liveReload": true
  }
}
```

**OpenClaw** — present on a connected node:

```text
canvas action:present target:http://<gateway-host>:18793/__openclaw__/canvas/index.html
```

**Hermes** — no `canvasHost`; open `index.html` locally if useful, otherwise keep Markdown reports. Do not invent `/__openclaw__/` URLs.

Sample payload (no DB): `runtimes/openclaw/canvas/pmgo/data.sample.json`  
Operator notes: `runtimes/openclaw/canvas/README.md`

## Delivery sketch

1. Agent (or cron) runs `pmgo_canvas_render` / `npm run canvas:render`.
2. OpenClaw serves `index.html` from `canvasHost.root` and live-reloads on file change.
3. Canvas updates are announce-only; writes still go through policy-gated MCP tools.

## Status

**Data export + OpenClaw HTML render template shipped.** Re-run render to refresh charts; Hermes continues to use Markdown weekly reports.
