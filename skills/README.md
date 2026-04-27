# Skills Pack Scaffold

The `skills/` directory hosts MCP-compatible capabilities for `pmgo`.

Shipped in tree (code or docs):

- `project-core` — Python store + `scripts/project-core.py` CLI against `memory/pmgo.db` (OpenClaw/MCP wiring later)
- `daily-standup` — `scripts/daily-standup.py` CLI + `memory/templates/daily-standup.*.md`
- `weekly-report` — `scripts/weekly-report.py` CLI + `memory/templates/weekly-report.*.md`
- `integration-github` — `scripts/github-issues.py` for Issues REST + optional `import-task` into SQLite (`GITHUB_TOKEN`, `GITHUB_REPO`)
- `risk-radar` — `scripts/risk-radar.py` JSON scan: open/watching `risks` + `blocked` tasks per project (MCP: `pmgo_risk_scan`)
- **MCP (OpenClaw)** — `scripts/pmgo_mcp_server.py` stdio tool server (see `openclaw/README.md`)

Planned modules include:

- `integration-jira`
- `integration-linear`
- `integration-notion`
- `integration-feishu`
- `integration-dingtalk`

Each skill should include its own `SKILL.md` and implementation files.
