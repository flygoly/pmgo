# Hermes integration (pmgo)

Connect **pmgo** to [Hermes Agent](https://github.com/NousResearch/hermes-agent): register the same **stdio MCP server**, load persona files, and schedule reports with **Hermes cron**.

Upstream: [Native MCP client](https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/mcp/mcp-native-mcp) · [Migrate from OpenClaw](https://hermes-agent.nousresearch.com/docs/guides/migrate-from-openclaw) · [Feishu / Lark](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu)

Dual-runtime overview: [../README.md](../README.md) · OpenClaw guide: [../openclaw/README.md](../openclaw/README.md)

---

## 1) Install dependencies

```bash
pip install -e ".[mcp]"
# Hermes itself: see https://hermes-agent.nousresearch.com/docs
```

---

## 2) Register the pmgo MCP server

Hermes reads `mcp_servers` from `~/.hermes/config.yaml`. Field names match OpenClaw (`command`, `args`, `env`, `cwd`).

**Generate snippet** (recommended):

```bash
export PMGO_ROOT="/absolute/path/to/pmgo"
npm run runtime:config -- --runtime hermes
```

**Or add manually** to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  pmgo:
    command: python3
    args:
      - /absolute/path/to/pmgo/scripts/pmgo_mcp_server.py
    env:
      PMGO_WORKSPACE: /absolute/path/to/pmgo
      PMGO_DEFAULT_PROJECT_ID: "<uuid>"
      PMGO_DEFAULT_LOCALE: zh-CN
```

See [shared/mcp.env.example](../../shared/mcp.env.example) for all optional keys.

Restart Hermes or start a **new session** after MCP config changes so tools are discovered.

**Policy:** same as OpenClaw — `confirmed: true` for gated writes (`policy/pmgo.policy.yaml`).

---

## 3) Load persona

### Option A — Migrate from OpenClaw

If you already run pmgo on OpenClaw:

```bash
hermes claw migrate --dry-run
hermes claw migrate --preset full --migrate-secrets
```

MCP servers, `SOUL.md`, `AGENTS.md`, memories, and channel tokens map automatically. `IDENTITY.md` and `TOOLS.md` are archived — merge important bits into `SOUL.md` if needed.

### Option B — Fresh Hermes setup

Copy persona into Hermes layout:

| pmgo file | Hermes destination |
| --- | --- |
| `agent/SOUL.md` | `~/.hermes/SOUL.md` (merge `agent/IDENTITY.md` if desired) |
| `agent/AGENTS.md` | workspace `AGENTS.md` (`hermes claw migrate --workspace-target`) |
| `agent/USER.md` | `~/.hermes/memories/USER.md` |

Locale overlays (`agent/locales/zh-CN/`) are not auto-imported — merge into `SOUL.md` or maintain parallel context files.

---

## 4) Connect Feishu / Lark (recommended for CN teams)

```bash
hermes gateway setup   # choose Feishu, websocket mode
```

Environment (see [Feishu docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu)):

```bash
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=secret_xxx
FEISHU_DOMAIN=feishu
FEISHU_CONNECTION_MODE=websocket
FEISHU_HOME_CHANNEL=oc_xxx   # cron / notification target
```

Telegram, Discord, Slack, WhatsApp, and Signal are also supported.

---

## 5) Cron

Use **`hermes cron create`** (not `cron/jobs.yaml` in this repo).

Shared agent messages: [shared/cron-messages.md](../../shared/cron-messages.md)  
Shell examples: [cron.examples.sh](./cron.examples.sh)

For Feishu delivery, set `FEISHU_HOME_CHANNEL` or use `/set-home` in chat.

---

## 6) Verify

```bash
hermes mcp list    # or check config.yaml mcp_servers
npm run mcp:pmgo:check
npm run validate
```

In chat, ask the agent to call `pmgo_project_list` or `pmgo_daily_report`.

---

## 7) Troubleshooting

- **MCP tools missing:** confirm `mcp_servers.pmgo` in config, restart gateway, start new session.
- **Policy / confirmed:** re-invoke tool with `confirmed=true` after user approval.
- **Skills from `skills/`:** pmgo skills are exposed via MCP, not copied to `~/.hermes/skills/` — register MCP only.
- **Dual stack with OpenClaw:** share one `PMGO_WORKSPACE` and `memory/pmgo.db`; do not run two MCP servers writing the same DB concurrently.

## Hermes-only features

- **GEPA** self-improving skills — complementary to pmgo’s static `SKILL.md` pack.
- **Tirith** pre-execution scanning for tool calls.

## Not available on Hermes

- OpenClaw **Live Canvas** (M3 Gantt/burndown) — use Markdown reports from `pmgo_daily_report` / `pmgo_weekly_report` instead.
