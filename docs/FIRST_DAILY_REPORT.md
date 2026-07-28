# From zero to first daily report

Shortest path on a developer machine. Uses **CLI** first (no gateway required), then optional OpenClaw **or** Hermes registration.

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

## 4. (Optional) Wire a gateway

Pick **one** runtime — same MCP server, same SQLite.

**OpenClaw**

```bash
npm run setup -- --runtime openclaw
npm run doctor -- --runtime openclaw
npm run start -- --runtime openclaw
```

**Hermes**

```bash
npm run setup -- --runtime hermes
npm run doctor -- --runtime hermes
npm run start -- --runtime hermes
```

`setup` installs missing MCP dependencies, applies the runtime registration, and
installs the pmgo persona/agent. It is safe to repeat. Preview it with `--dry-run`.
For manual configuration, use `npm run runtime:config -- --runtime ...`.

Then in chat: ask pmgo to call `pmgo_daily_report`.

## 5. (Optional) Channel delivery

| Runtime | Guide |
| --- | --- |
| OpenClaw | [runtimes/openclaw/telegram-e2e.md](../runtimes/openclaw/telegram-e2e.md) |
| Hermes | [runtimes/hermes/feishu-e2e.md](../runtimes/hermes/feishu-e2e.md) |
