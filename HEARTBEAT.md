# Heartbeat and scheduled reports

- **OpenClaw Gateway** heartbeat, cron, and channel defaults are **not** controlled by this file. They live in your OpenClaw Gateway configuration (per-[Heartbeat](https://docs.openclaw.ai/gateway/heartbeat) and [cron jobs](https://docs.openclaw.ai/automation/cron-jobs)).

- **This repository** can still use `HEARTBEAT.md` as a *local checklist* the agent (or you) can edit. Keep it small: reminders to run `npm run validate`, to check blockers, or to paste a one-line “what to do on the next heartbeat” note.

- **Daily / weekly Markdown** generation is implemented by `scripts/daily-standup.py` and `scripts/weekly-report.py`, and is exposed to OpenClaw via **`scripts/pmgo_mcp_server.py`** (see `openclaw/README.md` for registering the server and for **`openclaw cron add`** examples that deliver to Telegram or other channels).

- The **`cron/jobs.yaml`** file at the repo root is a **reference sketch** of intended automations, not a runtime consumed by OpenClaw. Real schedules should be created with **`openclaw cron add`**.

## Example local checklist (optional)

```markdown
# Next heartbeat
# - [ ] Skim `memory/pmgo.db` blockers (or ask pmgo to use pmgo_task_list)
# - [ ] Re-run `npm run validate` before pushing
```
