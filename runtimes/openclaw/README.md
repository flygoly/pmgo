# OpenClaw integration (pmgo)

Connect the **pmgo** workspace to an **OpenClaw Gateway**: register the policy-aware **MCP server**, enable IM channels, and schedule reports with Gateway **cron**.

Upstream: [MCP CLI](https://docs.openclaw.ai/cli/mcp) · [Gateway tools](https://docs.openclaw.ai/gateway/config-tools) · [Channels](https://docs.openclaw.ai/gateway/config-channels) · [Cron jobs](https://docs.openclaw.ai/automation/cron-jobs)

Dual-runtime overview: [../README.md](../README.md) · Hermes guide: [../hermes/README.md](../hermes/README.md)

---

## 1) Install MCP dependencies

From the pmgo repository root:

```bash
pip install -e ".[mcp]"
# or: pip install mcp pyyaml
```

---

## 2) Register the pmgo stdio MCP server

Use an **absolute path** to `scripts/pmgo_mcp_server.py`. Set `PMGO_WORKSPACE` to the repo root.

**Generate config** (recommended):

```bash
export PMGO_ROOT="/absolute/path/to/pmgo"
npm run runtime:config -- --runtime openclaw
```

**Or register manually:**

```bash
export PMGO_ROOT="/absolute/path/to/pmgo"
openclaw mcp set pmgo "$(jq -n \
  --arg cmd "$(command -v python3)" \
  --arg script "$PMGO_ROOT/scripts/pmgo_mcp_server.py" \
  --arg root "$PMGO_ROOT" \
  '{command: $cmd, args: [$script], env: {PMGO_WORKSPACE: $root}}')"
openclaw mcp show pmgo --json
```

Add optional integration keys to the `env` object — see [shared/mcp.env.example](../../shared/mcp.env.example).

**Policy:** writes require `confirmed: true` when `policy/pmgo.policy.yaml` sets `require_confirm: true`.

**Tools:** `pmgo_project_*`, `pmgo_task_*`, `pmgo_milestone_*`, `pmgo_risk_*`, `pmgo_daily_report`, `pmgo_weekly_report`, `pmgo_github_*`, `pmgo_linear_*`, `pmgo_jira_*`.

GTD walkthrough: [gtd-quickstart.md](./gtd-quickstart.md)

---

## 3) Import the pmgo agent

```bash
openclaw agent add ./agent
```

Persona: `agent/SOUL.md`, `AGENTS.md`, `USER.md`, plus `agent/locales/{zh-CN,zh-TW}/` overlays.

---

## 4) Connect a channel (Telegram example)

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

Feishu and other providers: `channels.*` in OpenClaw config ([config-channels](https://docs.openclaw.ai/gateway/config-channels)).

---

## 5) Cron / heartbeat

Production schedules use **`openclaw cron add`**, not `cron/jobs.yaml` in this repo (narrative reference only).

Shared agent messages: [shared/cron-messages.md](../../shared/cron-messages.md)  
Shell examples: [cron.examples.sh](./cron.examples.sh)

Heartbeat for main-session polling: [Gateway heartbeat](https://docs.openclaw.ai/gateway/heartbeat) and repo `HEARTBEAT.md`.

---

## 6) Verify

```bash
openclaw mcp list          # should include pmgo
npm run mcp:pmgo:check
npm run validate
```

---

## 7) Troubleshooting

- **MCP import errors:** `pip install mcp pyyaml` in the Python used by the server command.
- **Policy / confirmed:** re-invoke with `confirmed=true` after user approval.
- **Empty GitHub results:** set `GITHUB_TOKEN` + `GITHUB_REPO` in MCP `env`.
- **Cron delivery:** check `--announce` / `--channel` / `--to` ([cron delivery](https://docs.openclaw.ai/automation/cron-jobs#delivery-and-output)).
