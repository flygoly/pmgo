# OpenClaw integration (pmgo)

This folder documents how to connect the **pmgo** workspace to a local or remote **OpenClaw Gateway**: register the **pmgo MCP server** (policy-aware tools), enable an **IM channel** (Telegram example), and schedule **daily / weekly** briefs with **Gateway cron** (not the small `cron/jobs.yaml` sample in the repo root—that file is a narrative reference only).

Upstream references: [MCP CLI](https://docs.openclaw.ai/cli/mcp), [Gateway tools](https://docs.openclaw.ai/gateway/config-tools), [Channels](https://docs.openclaw.ai/gateway/config-channels), [Scheduled tasks](https://docs.openclaw.ai/automation/cron-jobs).

---

## 1) Install MCP dependencies (pmgo repo)

From the pmgo repository root:

```bash
pip install -e ".[mcp]"
# or: pip install mcp pyyaml
```

This provides the `mcp` Python package (FastMCP stdio server) and PyYAML for reading `policy/pmgo.policy.yaml` inside `scripts/pmgo_mcp_server.py`.

---

## 2) Register the pmgo stdio MCP server

Use an **absolute path** to `scripts/pmgo_mcp_server.py`. Set `PMGO_WORKSPACE` to the same repo root so the server can find `memory/`, `policy/`, and `locales/`.

**Example (macOS / Linux, JSON passed to `openclaw mcp set`):**

```bash
export PMGO_ROOT="/absolute/path/to/pmgo"
openclaw mcp set pmgo "$(jq -n \
  --arg cmd "$(command -v python3)" \
  --arg script "$PMGO_ROOT/scripts/pmgo_mcp_server.py" \
  --arg root "$PMGO_ROOT" \
  '{command: $cmd, args: [$script], env: {PMGO_WORKSPACE: $root}}')"
openclaw mcp show pmgo --json
```

Add **GitHub** credentials to the same `env` object if you use GitHub tools from the agent (optional):

```text
"GITHUB_TOKEN": "ghp_...",
"GITHUB_REPO": "owner/name"
```

**Policy model:** every tool first checks `policy/pmgo.policy.yaml` via `scripts/pmgo_policy.py`. Writes (`project`/`task` creation, GitHub create/close/import) require `confirmed: true` in the tool arguments when the policy entry sets `require_confirm: true` (mirrors human approval in chat before the model re-calls the tool with `confirmed: true`).

**Tool names** exposed by the server include: `pmgo_project_list`, `pmgo_project_create`, `pmgo_task_list`, `pmgo_task_create`, `pmgo_risk_scan`, `pmgo_daily_report`, `pmgo_weekly_report`, `pmgo_github_issue_list`, `pmgo_github_issue_get`, `pmgo_github_issue_create`, `pmgo_github_issue_close`, `pmgo_github_import_task`, `pmgo_linear_issue_list`, `pmgo_linear_issue_get`, `pmgo_linear_import_task`.

Embedded/bundled MCP runtimes are controlled by OpenClaw `tools` profiles; if MCP tools are missing in the agent, check `tools.deny` / `tools.profile` in Gateway config and ensure MCP bundles are not disabled (see [config-tools](https://docs.openclaw.ai/gateway/config-tools)).

---

## 3) Connect one IM channel (Telegram example)

Minimal **Telegram** block (from [config-channels](https://docs.openclaw.ai/gateway/config-channels)):

```json5
{
  channels: {
    telegram: {
      enabled: true,
      botToken: "123456:ABCDEF", // or tokenFile: "/path/to/telegram_token.txt"
      dmPolicy: "pairing",
      allowFrom: ["tg:YOUR_NUMERIC_ID"],
    },
  },
}
```

- Create a bot with **@BotFather**, then paste the token.  
- Use `dmPolicy: "pairing"` for safety; complete pairing from chat before routing production traffic.  
- **Feishu** / other providers: use the same Gateway config layout under `channels.*` in your OpenClaw config file.

Point your **pmgo agent** at this Gateway (e.g. `openclaw agents add …` with workspace = pmgo) so sessions receive channel routes for `messages_send` and cron `announce` delivery.

---

## 4) Daily / weekly reports with Gateway cron

OpenClaw **cron** is owned by the Gateway (see [cron-jobs](https://docs.openclaw.ai/automation/cron-jobs)). Prefer **`openclaw cron add`** over editing files in the pmgo repo for production schedules.

**Pattern:** an **isolated** session with a **message** that tells the **pmgo** agent to call MCP tools, plus optional **`--announce`** to deliver the final reply to Telegram (or another channel) when the run finishes.

**Daily (weekdays 09:00, Asia/Shanghai):**

```bash
openclaw cron add \
  --name "pmgo-daily-standup" \
  --cron "0 9 * * 1-5" \
  --tz "Asia/Shanghai" \
  --session isolated \
  --agent <pmgo-agent-id> \
  --message "You are pmgo. Use the pmgo MCP tools. Call pmgo_daily_report with the user's default project_id and locale zh-CN, then post a concise summary. If a tool returns policy text asking for confirmation, ask the user in chat and stop." \
  --announce --channel telegram --to "123456789"
```

(Replace `123456789` with your DM id or a group / topic id from Gateway docs. Use `session:standup` if you want the same conversation across runs.)

**Weekly (Fridays 17:00, UTC week alignment matches `weekly_report` implementation):**

```bash
openclaw cron add \
  --name "pmgo-weekly-report" \
  --cron "0 17 * * 5" \
  --tz "UTC" \
  --session isolated \
  --agent <pmgo-agent-id> \
  --message "You are pmgo. Use pmgo_weekly_report for the main project (project_id=..., locale=en). Summarize top risks and next actions. Keep under 300 words." \
  --announce --channel telegram --to "123456789"
```

**Heartbeat vs cron:** [Gateway heartbeat](https://docs.openclaw.ai/gateway/heartbeat) is for **main session** periodic turns. Scheduled **reports** are usually better as **isolated** cron so each run has a clean transcript. Edit the repo’s `HEARTBEAT.md` only if you use *workspace-local* heartbeats; Gateway behaviour is configured in OpenClaw config, not in this repository.

---

## 5) Verify

- `openclaw mcp list` should include `pmgo`.  
- `npm run mcp:pmgo:check` in this repo checks that `mcp` + `pyyaml` import (CI installs them).  
- `python3 scripts/pmgo_mcp_server.py` should stay running on stdio (used by the Gateway, not for manual use).

---

## 6) Troubleshooting

- **MCP import errors:** `pip install mcp pyyaml` in the same Python that runs the server command.  
- **“Policy denies” / “set confirmed”:** match behaviour to `policy/pmgo.policy.yaml` and re-invoke with `confirmed=true` after the user approves.  
- **Empty GitHub results:** set `GITHUB_TOKEN` + `GITHUB_REPO` in the MCP `env` block.  
- **No Telegram delivery from cron:** ensure `--announce` / `--channel` / `--to` match a routable target and the Gateway has a live channel session; see [cron-jobs delivery](https://docs.openclaw.ai/automation/cron-jobs#delivery-and-output).
