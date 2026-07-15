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

## Scaffold / planned

- `integration-feishu` — tenant token smoke CLI (`npm run feishu:smoke`)
- `integration-notion` — users/me smoke CLI (`npm run notion:smoke`)
- `integration-dingtalk` — docs only until M3 client lands

Each skill should include its own `SKILL.md` and implementation files.
