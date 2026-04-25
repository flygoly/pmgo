# Skills Pack Scaffold

The `skills/` directory hosts MCP-compatible capabilities for `pmgo`.

Shipped in tree (code or docs):

- `project-core` — Python store + `scripts/project-core.py` CLI against `memory/pmgo.db` (OpenClaw/MCP wiring later)
- `daily-standup` — `scripts/daily-standup.py` CLI + `memory/templates/daily-standup.*.md`
- `weekly-report` — `scripts/weekly-report.py` CLI + `memory/templates/weekly-report.*.md`

Planned modules include:

- `daily-standup`
- `risk-radar`
- `weekly-report`
- `integration-github`
- `integration-jira`
- `integration-linear`
- `integration-notion`
- `integration-feishu`
- `integration-dingtalk`

Each skill should include its own `SKILL.md` and implementation files.
