#!/usr/bin/env bash
# OpenClaw cron examples for pmgo. Requires openclaw CLI and a registered pmgo MCP server.
# Agent messages are shared with Hermes — see shared/cron-messages.md
set -euo pipefail

: "${PMGO_AGENT_ID:?Set PMGO_AGENT_ID to your OpenClaw pmgo agent id}"
: "${TELEGRAM_TO:?Set TELEGRAM_TO to your Telegram DM or group id}"

DAILY_MSG='You are pmgo. Use the pmgo MCP tools. Call pmgo_daily_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Post a concise summary: done / in progress / blockers / next actions. If a tool returns policy text asking for confirmation, ask the user in chat and stop.'

WEEKLY_MSG='You are pmgo. Call pmgo_weekly_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Summarize overall status, top risks, and next actions. Keep under 300 words.'

echo "== Daily standup (weekdays 09:00 Asia/Shanghai) =="
echo openclaw cron add \\
  --name \"pmgo-daily-standup\" \\
  --cron \"0 9 * * 1-5\" \\
  --tz \"Asia/Shanghai\" \\
  --session isolated \\
  --agent \"$PMGO_AGENT_ID\" \\
  --message \"$DAILY_MSG\" \\
  --announce --channel telegram --to \"$TELEGRAM_TO\"

echo
echo "== Weekly report (Fridays 17:00 UTC) =="
echo openclaw cron add \\
  --name \"pmgo-weekly-report\" \\
  --cron \"0 17 * * 5\" \\
  --tz \"UTC\" \\
  --session isolated \\
  --agent \"$PMGO_AGENT_ID\" \\
  --message \"$WEEKLY_MSG\" \\
  --announce --channel telegram --to \"$TELEGRAM_TO\"
