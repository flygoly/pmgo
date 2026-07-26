# OpenClaw Live Canvas (pmgo)

Self-contained HTML template that renders `pmgo.canvas.snapshot/v1` (Gantt + burndown).

## Quick path

```bash
# From pmgo repo root
npm run canvas:render -- --from-first-project
# Writes reports/canvas/pmgo/{index.html,data.json}
```

Point OpenClaw `canvasHost.root` at that output directory (or copy `reports/canvas/pmgo/*` into your canvas root):

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

Present on a connected node:

```text
canvas action:present target:http://<gateway-host>:18793/__openclaw__/canvas/index.html
```

Preview sample data without a DB:

```bash
cp runtimes/openclaw/canvas/pmgo/data.sample.json /tmp/pmgo-canvas/data.json
cp runtimes/openclaw/canvas/pmgo/index.html /tmp/pmgo-canvas/
# open /tmp/pmgo-canvas/index.html in a browser, or serve that folder as canvasHost.root
```

Full notes: [docs/LIVE_CANVAS.md](../../../docs/LIVE_CANVAS.md).
