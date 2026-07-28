# Feishu / Lark E2E acceptance (Hermes)

Goal: prove a new user can **create a project → add a task → receive a daily report** over Feishu (or Lark).

This is the Hermes IM channel path (parity with [OpenClaw Telegram E2E](../openclaw/telegram-e2e.md)).  
Same MCP tools; different gateway channel.

> Two Feishu layers (do not mix them up):
>
> 1. **Gateway channel** — chat + cron delivery (`FEISHU_APP_ID` / websocket). Official Hermes messaging.
> 2. **pmgo skill** — optional tasklist import (`FEISHU_TASKLIST_GUID` in MCP `env`). Not required for this E2E.

## Prerequisites

- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed; gateway can start
- Feishu/Lark app with bot capability (see [Hermes Feishu docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu))
- `lark-oapi` + `websockets` available in the Hermes Python env (`pip install lark-oapi websockets`)
- pmgo cloned; `pip install '.[mcp]'` (PyYAML needed for `runtime:config --runtime hermes`)
- Home chat for cron (optional): `FEISHU_HOME_CHANNEL` or `/set-home` in chat

## Checklist

### A. Local memory + MCP

```bash
cd /absolute/path/to/pmgo
npm run gtd:bootstrap -- --name "Feishu E2E" --locale zh-CN
# eval printed exports (PMGO_WORKSPACE, PMGO_DEFAULT_PROJECT_ID, …)

# Optional: also export skill keys if you will test pmgo_feishu_* later
# export FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_TASKLIST_GUID=…

npm run setup -- --runtime hermes
npm run doctor -- --runtime hermes
```

The setup command registers MCP and installs the pmgo persona. Alternatively,
use `hermes claw migrate` if you already run OpenClaw.

Restart the gateway / open a **new session** so MCP tools are discovered.

```bash
hermes mcp list    # expect pmgo
npm run mcp:pmgo:check
```

### B. Connect Feishu channel (gateway)

```bash
hermes gateway setup   # choose Feishu, websocket mode
```

Typical env (channel — not the same as MCP skill env, though App ID/Secret often match):

```bash
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=secret_xxx
export FEISHU_DOMAIN=feishu          # or: lark
export FEISHU_CONNECTION_MODE=websocket
# export FEISHU_HOME_CHANNEL=oc_xxx  # cron / home chat
```

Start the gateway (`hermes gateway` or your service install), then DM the bot (or @mention in an allowed group).

### C. Chat acceptance (Feishu)

In Feishu with your Hermes bot:

1. **List projects** — ask: “列出我的 pmgo 项目” / “List my pmgo projects”  
   Expect: agent calls `pmgo_project_list` and shows the bootstrap project.

2. **Create a task** — ask: “创建任务：E2E standup demo，状态 doing”  
   Expect: confirmation if policy requires it; then `pmgo_task_create` with `confirmed=true`.

3. **Daily report** — ask: “生成今日站会” / “Generate today’s standup”  
   Expect: `pmgo_daily_report` Markdown with the new task under today / in progress.

4. **Risk scan** — ask: “扫描阻塞” / “Scan blockers”  
   Expect: `pmgo_risk_scan` summary (may be empty).

### D. Scheduled delivery (optional)

```bash
export HERMES_TIMEZONE=Asia/Shanghai
export HERMES_CRON_DELIVER=origin    # or platform-specific target; see hermes cron create --help
export PMGO_WORKSPACE="/absolute/path/to/pmgo"
npm run cron:config -- --runtime hermes
# run the printed hermes cron create … commands
```

Prefer home chat: set `FEISHU_HOME_CHANNEL` or `/set-home`, then confirm a job with `hermes cron list`.  
Or use [cron.examples.sh](./cron.examples.sh).

### E. Optional — pmgo Feishu task skill

Only if you want tasklist import (separate from chat E2E):

```bash
# Ensure FEISHU_APP_ID / SECRET / TASKLIST_GUID are in mcp_servers.pmgo.env
# (re-run runtime:config after exporting them)
# In chat: ask to list Feishu tasks / import one into pmgo
```

CLI smoke without chat: `npm run feishu:smoke`.

### F. Regression (local, no Feishu)

```bash
npm run validate
npm run daily-standup -- report
```

Record pass/fail for steps C1–C3 when claiming Hermes IM E2E closure.

## Failure points

| Symptom | Likely cause |
| --- | --- |
| MCP tools missing | `mcp_servers.pmgo` not merged / no new session / wrong `PMGO_WORKSPACE` |
| Bot silent in Feishu | Channel not set up; websocket deps missing; app scopes / event subscribe |
| Policy confirmation loop | User must approve in chat before `confirmed=true` |
| Empty report | No `PMGO_DEFAULT_PROJECT_ID` or wrong project |
| Cron silent | Gateway not running; no home channel; wrong `HERMES_TIMEZONE` |
| `pmgo_feishu_*` fails but chat works | Skill env missing in MCP block (channel env ≠ MCP env) |

## Out of scope

- OpenClaw Feishu channel (use OpenClaw `@openclaw/feishu` + same MCP tools)
- Live Canvas present URLs (Hermes has no canvasHost — use Markdown reports)
- Full Feishu Bitable / doc sync (M3 deepening)
