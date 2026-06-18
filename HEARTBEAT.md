# Heartbeat and scheduled reports

- **Gateway** heartbeat, cron, and channel defaults are **not** controlled by this file. Configure them in OpenClaw or Hermes (see [runtimes/README.md](./runtimes/README.md)).

- **This repository** can still use `HEARTBEAT.md` as a *local checklist* the agent (or you) can edit. Keep it small: reminders to run `npm run validate`, to check blockers, or to paste a one-line “what to do on the next heartbeat” note.

- **Daily / weekly Markdown** is implemented by `scripts/daily-standup.py` and `scripts/weekly-report.py`, exposed via **`scripts/pmgo_mcp_server.py`**:
  - OpenClaw: [runtimes/openclaw/README.md](./runtimes/openclaw/README.md) · `openclaw cron add`
  - Hermes: [runtimes/hermes/README.md](./runtimes/hermes/README.md) · `hermes cron create`

- **`cron/jobs.yaml`** is a **reference sketch** only. Production schedules use gateway cron CLI; shared agent messages live in [shared/cron-messages.md](./shared/cron-messages.md).

## Example local checklist (optional)

```markdown
# Next heartbeat
# - [ ] Skim `memory/pmgo.db` blockers (or ask pmgo to use pmgo_task_list)
# - [ ] Re-run `npm run validate` before pushing
```
