#!/usr/bin/env bash
# Hermes cron examples for pmgo. Requires hermes CLI and mcp_servers.pmgo in config.
# Agent messages are shared with OpenClaw — see shared/cron-messages.md
set -euo pipefail

DAILY_MSG='You are pmgo. Use the pmgo MCP tools. Call pmgo_daily_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Post a concise summary: done / in progress / blockers / next actions. If a tool returns policy text asking for confirmation, ask the user in chat and stop.'

WEEKLY_MSG='You are pmgo. Call pmgo_weekly_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Summarize overall status, top risks, and next actions. Keep under 300 words.'

echo "== Hermes cron examples (adjust flags to your hermes version) =="
echo
echo "# Daily standup — weekdays 09:00 Asia/Shanghai"
echo hermes cron create \\
  --name pmgo-daily-standup \\
  --schedule \"0 9 * * 1-5\" \\
  --timezone Asia/Shanghai \\
  --message \"$DAILY_MSG\"
echo
echo "# Weekly report — Fridays 17:00 UTC"
echo hermes cron create \\
  --name pmgo-weekly-report \\
  --schedule \"0 17 * * 5\" \\
  --timezone UTC \\
  --message \"$WEEKLY_MSG\"
echo
echo "# Feishu: set FEISHU_HOME_CHANNEL or use /set-home for delivery target"
echo "# See: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu"
