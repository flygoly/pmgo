# Shared cron agent messages (OpenClaw & Hermes)

Use the same **message** body when scheduling daily/weekly runs; only the CLI wrapper differs (`openclaw cron add` vs `hermes cron create`). Set `PMGO_DEFAULT_PROJECT_ID` and `PMGO_DEFAULT_LOCALE` in the MCP server `env` so prompts do not hard-code UUIDs.

## Daily standup (weekdays)

```
You are pmgo. Use the pmgo MCP tools. Call pmgo_daily_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Highlight stale blockers (>24h) and open risks. Summarize blockers and next actions. If a tool returns policy text asking for confirmation, ask the user in chat and stop.
```

**Schedule hint:** `0 9 * * 1-5`, timezone `Asia/Shanghai` (adjust as needed).

## Weekly report (Fridays)

```
You are pmgo. Call pmgo_weekly_report (locale from PMGO_DEFAULT_LOCALE), then pmgo_risk_scan. Summarize overall status, top risks, and next actions. Keep under 300 words.
```

**Schedule hint:** `0 17 * * 5`, timezone `UTC` (matches weekly report UTC week boundaries).

## Blocker scan (optional, mid-day)

```
You are pmgo. Call pmgo_risk_scan with auto_escalate=true and confirmed=true when the user has approved escalation; otherwise scan only. If any task has been blocked >24h, list severity and recommend escalation options. Keep under 150 words.
```

See executable examples:

- [runtimes/openclaw/cron.examples.sh](../runtimes/openclaw/cron.examples.sh)
- [runtimes/hermes/cron.examples.sh](../runtimes/hermes/cron.examples.sh)
