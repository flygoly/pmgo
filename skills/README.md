# Skills Pack

The `skills/` directory hosts MCP-compatible capabilities for `pmgo`.

## Shipped

- `project-core` — SQLite store + CLI + MCP CRUD for projects/tasks/milestones/risks/decisions
- `daily-standup` — Markdown daily report from DB
- `weekly-report` — Weekly status Markdown (fills evidence URLs from imported task details when present)
- `risk-radar` — Blocker/risk scan + optional escalate
- `integration-github` — Issues REST + import/sync (paginated)
- `integration-linear` — GraphQL list/get + import (cursor pagination)
- `integration-jira` — Cloud REST list/get/import + transitions
- **MCP hub** — `scripts/pmgo_mcp_server.py` (policy-gated)

## Scaffold / deepening

- `integration-feishu` — tasklist list/get/import + MCP
- `integration-notion` — database query / import + MCP (`NOTION_DATABASE_ID`)
- `integration-dingtalk` — access token smoke (`npm run dingtalk:smoke`)
- `canvas-data` — Live Canvas Gantt/burndown JSON (`npm run canvas`)
- `project-core` also covers **people** / **retrospectives** CRUD

Each skill should include its own `SKILL.md` and implementation files.
