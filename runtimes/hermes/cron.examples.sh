#!/usr/bin/env bash
# Hermes cron examples for pmgo. Requires hermes CLI and mcp_servers.pmgo in config.
# Agent messages are shared with OpenClaw — see shared/cron-messages.md
#
# Upstream CLI (hermes cron create):
#   hermes cron create SCHEDULE [PROMPT] [--name ...] [--deliver ...] [--workdir ...]
# Schedule + prompt are positional. No --cron / --schedule / --message / --timezone.
# Timezone is gateway-global: HERMES_TIMEZONE or ~/.hermes/config.yaml timezone.
set -euo pipefail

DAILY_MSG='You are pmgo. Use the pmgo MCP tools. Call pmgo_daily_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Post a concise summary: done / in progress / blockers / next actions. If a tool returns policy text asking for confirmation, ask the user in chat and stop.'

WEEKLY_MSG='You are pmgo. Call pmgo_weekly_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Summarize overall status, top risks, and next actions. Keep under 300 words.'

WORKDIR="${PMGO_WORKSPACE:-}"
DELIVER="${HERMES_CRON_DELIVER:-}"

echo "== Hermes cron examples (matches hermes cron create --help) =="
echo "# Prefer: npm run cron:config -- --runtime hermes"
echo "# Set HERMES_TIMEZONE=Asia/Shanghai (or config.yaml timezone) for weekday 09:00 intent"
echo

daily=(hermes cron create "0 9 * * 1-5" "$DAILY_MSG" --name pmgo-morning-briefing)
weekly=(hermes cron create "0 17 * * 5" "$WEEKLY_MSG" --name pmgo-weekly-report)
if [[ -n "$DELIVER" ]]; then
  daily+=(--deliver "$DELIVER")
  weekly+=(--deliver "$DELIVER")
fi
if [[ -n "$WORKDIR" ]]; then
  daily+=(--workdir "$WORKDIR")
  weekly+=(--workdir "$WORKDIR")
fi

echo "# Daily standup — weekdays 09:00 (interpret in HERMES_TIMEZONE)"
printf '%q ' "${daily[@]}"
echo
echo
echo "# Weekly report — Fridays 17:00 (same global timezone; adjust expr if you need UTC)"
printf '%q ' "${weekly[@]}"
echo
echo
echo "# Delivery: export HERMES_CRON_DELIVER=telegram   # or discord / platform:chat_id"
echo "# Feishu home: /set-home or FEISHU_HOME_CHANNEL — see Hermes Feishu docs"
echo "# Generate from jobs.yaml: npm run cron:config -- --runtime hermes"
