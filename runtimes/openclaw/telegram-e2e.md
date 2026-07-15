# Telegram E2E acceptance (OpenClaw)

Goal: prove a new user can **create a project → add a task → receive a daily report** over Telegram.

This is the M1 IM channel path. Feishu/DingTalk use the same MCP tools once the gateway channel is configured.

## Prerequisites

- OpenClaw installed and onboarded (`openclaw onboard`)
- Telegram bot connected in OpenClaw (see OpenClaw channel docs)
- pmgo cloned; Python venv with `pip install '.[mcp]'`
- Your Telegram DM or group id (`TELEGRAM_TO`)

## Checklist

### A. Local memory + MCP

```bash
cd /absolute/path/to/pmgo
npm run gtd:bootstrap -- --name "Telegram E2E" --locale en
# eval printed exports (PMGO_WORKSPACE, PMGO_DEFAULT_PROJECT_ID, …)

npm run runtime:config -- --runtime openclaw
# run the printed: openclaw mcp set pmgo …

openclaw agent add ./agent
openclaw mcp show pmgo --json   # confirm env has PMGO_WORKSPACE
```

### B. Chat acceptance (Telegram)

In a Telegram chat with your OpenClaw bot (or group where the bot can speak):

1. **List projects** — ask: “List my pmgo projects”  
   Expect: agent calls `pmgo_project_list` and shows the bootstrap project.

2. **Create a task** — ask: “Create a task titled E2E standup demo, status doing”  
   Expect: agent asks for confirmation if policy requires it; after you approve, `pmgo_task_create` with `confirmed=true`.

3. **Daily report** — ask: “Generate today’s standup”  
   Expect: `pmgo_daily_report` Markdown with the new task under today / in progress.

4. **Risk scan** — ask: “Scan blockers”  
   Expect: `pmgo_risk_scan` JSON or summary (may be empty).

### C. Scheduled delivery (optional)

```bash
export PMGO_AGENT_ID="<your-openclaw-agent-id>"
export TELEGRAM_TO="<chat-id>"
npm run cron:config -- --runtime openclaw
# run the printed openclaw cron add … commands
```

Or use [cron.examples.sh](./cron.examples.sh).

### D. Regression script (local, no Telegram)

When credentials are unavailable, CI-style smoke still covers memory + reports:

```bash
npm run validate
npm run daily-standup -- report
```

Record pass/fail for steps B1–B3 in the PR or release notes when claiming M1 IM closure.

## Failure points

| Symptom | Likely cause |
| --- | --- |
| MCP tools missing | MCP not registered / wrong `PMGO_WORKSPACE` |
| Policy confirmation loop | User must approve in chat before `confirmed=true` |
| Empty report | No `PMGO_DEFAULT_PROJECT_ID` or wrong project |
| Cron silent | Wrong `--to` / agent id / timezone |

## Out of scope

- Feishu channel setup (same MCP tools; different OpenClaw channel plugin)
- Bidirectional task sync from Telegram messages into SQLite without agent tools
