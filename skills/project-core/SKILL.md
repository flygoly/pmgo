# project-core

Core skill for project and task lifecycle management.

## Responsibilities

- Create/read/update/list projects
- Create/read/update/list tasks
- Manage status transitions (`todo`, `doing`, `blocked`, `done`, `cancelled`)
- Attach dependency metadata

## Input contract

- Required fields are validated before write operations.
- External ids (`external_id`) are treated as idempotency keys.

## Safety rules

- Destructive operations require explicit confirmation.
- Cross-project moves require the target project to exist.
