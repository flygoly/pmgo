# Personal GTD quickstart (pmgo + OpenClaw)

End-to-end flow: **bootstrap local memory → register MCP → import agent → optional Telegram cron**.

Prerequisites: [OpenClaw](https://openclaw.ai) installed (`npm i -g openclaw`), Python 3.11+, this repo cloned.

---

## 1) Bootstrap SQLite + Markdown (one command)

From the pmgo repository root:

```bash
python3 scripts/gtd-bootstrap.py --name "My GTD" --locale zh-CN
```

This runs DB init/migrate/verify, creates a **SQLite project** and linked **`memory/projects/<slug>/`** markdown templates, and prints JSON including `id` (project UUID).

Set defaults for reports and MCP tools:

```bash
export PMGO_DEFAULT_PROJECT_ID="<uuid-from-output>"
export PMGO_DEFAULT_LOCALE=zh-CN
export PMGO_WORKSPACE="/absolute/path/to/pmgo"
```

Equivalent npm scripts:

```bash
npm run gtd:bootstrap -- --name "My GTD" --locale zh-CN
# or full scaffold pipeline:
npm run memory:scaffold -- --project-name "My GTD" --locale zh-CN
```

---

## 2) Register the pmgo MCP server

```bash
pip install -e ".[mcp]"
export PMGO_ROOT="/absolute/path/to/pmgo"
openclaw mcp set pmgo "$(jq -n \
  --arg cmd "$(command -v python3)" \
  --arg script "$PMGO_ROOT/scripts/pmgo_mcp_server.py" \
  --arg root "$PMGO_ROOT" \
  --arg pid "$PMGO_DEFAULT_PROJECT_ID" \
  --arg loc "$PMGO_DEFAULT_LOCALE" \
  '{command: $cmd, args: [$script], env: {PMGO_WORKSPACE: $root, PMGO_DEFAULT_PROJECT_ID: $pid, PMGO_DEFAULT_LOCALE: $loc}}')"
openclaw mcp show pmgo --json
```

With `PMGO_DEFAULT_PROJECT_ID` set in the MCP `env` block, cron messages no longer need a hard-coded `project_id=...`.

---

## 3) Import the pmgo agent

```bash
cd /absolute/path/to/pmgo
openclaw agent add ./agent
```

Persona files live under `agent/` (English base + `agent/locales/{zh-CN,zh-TW}/` overlays).

---

## 4) Try the GTD loop locally (no Gateway)

```bash
# Create a task
npm run project-core -- task-create --project-id "$PMGO_DEFAULT_PROJECT_ID" --title "Review inbox"

# Daily / weekly / risk (uses PMGO_DEFAULT_PROJECT_ID when set)
npm run daily-standup -- report
npm run weekly-report -- report
npm run risk-radar -- report
```

Or pass `--project-id` explicitly, or use `--from-first-project` for CI smoke tests.

---

## 5) Connect Telegram (optional)

Add to OpenClaw Gateway config (see [config-channels](https://docs.openclaw.ai/gateway/config-channels)):

```json5
{
  channels: {
    telegram: {
      enabled: true,
      botToken: "123456:ABCDEF",
      dmPolicy: "pairing",
      allowFrom: ["tg:YOUR_NUMERIC_ID"],
    },
  },
}
```

Schedule weekday standup (no hard-coded project id when MCP env has `PMGO_DEFAULT_PROJECT_ID`):

```bash
openclaw cron add \
  --name "pmgo-daily-standup" \
  --cron "0 9 * * 1-5" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --agent <pmgo-agent-id> \
  --message "You are pmgo. Call pmgo_daily_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Summarize blockers and next actions." \
  --announce --channel telegram --to "123456789"
```

More Gateway details: [openclaw/README.md](./README.md).

---

## 6) Verify

```bash
npm run validate
openclaw mcp list   # should include pmgo
```
