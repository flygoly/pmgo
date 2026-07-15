# From zero to first daily report

Shortest path on a developer machine. Uses **CLI** first (no gateway required), then optional OpenClaw registration.

## 1. Clone and deps

```bash
cd /absolute/path/to/pmgo
python3 -m venv .venv && source .venv/bin/activate
pip install '.[mcp]'
```

## 2. Bootstrap

```bash
npm run gtd:bootstrap -- --name "My GTD" --locale en
```

Copy the printed `export` block (includes `PMGO_WORKSPACE`, `PMGO_DEFAULT_PROJECT_ID`, `PMGO_DEFAULT_LOCALE`).

## 3. Add a task and render standup

```bash
# Use project id from bootstrap output
npm run project-core -- task-create \
  --project-id "$PMGO_DEFAULT_PROJECT_ID" \
  --title "Ship first standup" \
  --status doing

npm run daily-standup -- report
```

You should see Markdown with today / blockers sections filled from SQLite.

## 4. (Optional) Wire OpenClaw MCP

```bash
npm run runtime:config -- --runtime openclaw
# Run the printed openclaw mcp set … command
openclaw agent add ./agent
```

Then in chat: ask pmgo to call `pmgo_daily_report`.

## 5. (Optional) Telegram delivery

Follow [runtimes/openclaw/telegram-e2e.md](../runtimes/openclaw/telegram-e2e.md).
