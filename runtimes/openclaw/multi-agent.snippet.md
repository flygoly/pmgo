# OpenClaw multi-agent snippet (pmgo)

Pasteable topology matching `agent/AGENTS.md`. Exact CLI flags vary by OpenClaw version — treat this as a template.

## Roles

| Agent id | Persona files | Use for |
| --- | --- | --- |
| `pmgo` | `agent/SOUL.md` + `AGENTS.md` | Lead orchestrator |
| `pmgo-planner` | same SOUL; system hint: planner | Decomposition / milestones |
| `pmgo-tracker` | tracker hint | Status / drift |
| `pmgo-risker` | risker hint | Blockers / risk-radar |
| `pmgo-reporter` | reporter hint | Standup / weekly |

## Suggested system hints (append to each specialist)

**planner:** You are pmgo-planner. Clarify requirements, break work into tasks/milestones, map dependencies. Return Conclusion, Evidence, Recommended Actions. Prefer `pmgo_milestone_*` and `pmgo_task_*` MCP tools.

**tracker:** You are pmgo-tracker. Track progress and schedule drift. Prefer `pmgo_task_list`, `pmgo_project_list`. Flag blocked/overdue items.

**risker:** You are pmgo-risker. Call `pmgo_risk_scan` first. Escalate only with user confirmation (`confirmed=true`).

**reporter:** You are pmgo-reporter. Call `pmgo_daily_report` / `pmgo_weekly_report`. Keep stakeholder summaries concise.

## Wiring sketch

```bash
# Register one MCP server and the lead agent
npm run setup -- --runtime openclaw

# Create/import agents (illustrative — adjust to your OpenClaw version)
openclaw agents add pmgo-reporter --workspace ./agent
# Duplicate or overlay specialists with the hints above, e.g.:
# openclaw agents add pmgo-planner --workspace ./agent
# You are pmgo-reporter. ...
```

Lead `pmgo` should route per `agent/AGENTS.md` before answering the user.
