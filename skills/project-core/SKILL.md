# project-core

Core skill for project and task lifecycle management backed by the local **SQLite** database (`memory/pmgo.db`, schema in `memory/schema.sql`).

## Responsibilities

- Create/read/list projects
- Create/read/list/update tasks within a project
- Create/read/list/update milestones within a project
- Manage status transitions (`todo`, `doing`, `blocked`, `done`, `cancelled`)
- Optional markdown scaffold under `memory/projects/<slug>/` when creating a project
- Idempotency: integrations should set `source` + `external_id` on tasks when syncing from tools (unique per project when both set)

## Implementation (M1)

- Python package: `skills/project-core/project_core/`
- CLI entry: `python3 scripts/project-core.py` (also `npm run project-core -- …`)
- Markdown scaffold: `project_core/memory_md.py`
- Successful writes append a row to `audit_logs` with `actor = project-core` for traceability

## Tool surface (CLI + MCP)

| Command | Action |
| --- | --- |
| `project-list` | List all projects (JSON) |
| `project-create` | Create project: `--name`, optional `--slug`, `--description`, `--owner`, `--scaffold-markdown`, `--locale` |
| `task-list` | List tasks: required `--project-id`, optional `--status` |
| `task-create` | Create task: `--project-id`, `--title`, optional `--detail`, `--status`, `--priority`, `--assignee`, `--due-at`, `--milestone-id` |
| `task-update` | Update task: `--task-id` plus any fields to change |
| `milestone-list` | List milestones: `--project-id` |
| `milestone-create` | Create milestone: `--project-id`, `--title`, optional `--status`, `--owner`, `--due-at` |
| `milestone-update` | Update milestone: `--milestone-id` plus fields to change |

Global option: `--db PATH` to override the database file (else `PMGO_MEMORY_DB` or `memory/pmgo.db`).

MCP tools (via `scripts/pmgo_mcp_server.py`): `pmgo_project_create` (with `scaffold_markdown`), `pmgo_task_create`, `pmgo_task_update`, `pmgo_milestone_list`, `pmgo_milestone_create`, `pmgo_milestone_update`.

## Input contract

- Required fields are validated at the database layer (CHECK constraints).
- `external_id` (with `source`) is the idempotency key for imports (see unique index in schema).

## Safety rules

- Destructive operations (deletes) are not exposed in M1; add with explicit policy + confirmation in a later milestone.
- Cross-project task moves are not supported in M1.
- For automation, prefer reading task state before retrying a failed write.

## Smoke test

After `npm run memory:init` (or any path that creates `memory/pmgo.db`):

```bash
npm run project-core:smoke
```

## Future work

- People CRUD and task dependency links between tasks
- Risk/decision entity CRUD in project-core
