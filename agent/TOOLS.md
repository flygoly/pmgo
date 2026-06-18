# TOOLS - Tool Allowlist Policy

`pmgo` can only use controlled tools. Effective enforcement is defined in `policy/pmgo.policy.yaml` and applied inside `scripts/pmgo_mcp_server.py` (runtime-neutral).

## Design Principles

- Least privilege: default to read-only access.
- Auditability: external writes must be traceable.
- Confirmation: require explicit confirmation for risky actions.
- Recoverability: prefer reversible operations.

## Allowed by Default

- Project/task/milestone retrieval tools
- Reporting and summarization tools
- Template rendering and scoped memory read/write
- Read-only checks triggered by scheduler/heartbeat

## Require Confirmation

- `jira.create` and state transition writes
- `github.close_pr` and workflow-impacting writes
- `github.issue.create`, `github.issue.update`, `github.issue.import_task`, and `github.issue.sync` (Issues REST writes and local task import/sync)
- Broadcast messages to group channels
- Batch updates that may change ownership or schedule

## Disallowed by Default

- `shell.exec` (PM persona should not run arbitrary shell)
- Unscoped filesystem writes
- Destructive delete operations (e.g. `jira.delete`)
- Non-idempotent sync writes

## Idempotency and Audit Constraints

- Use `external_id` as deduplication key for integrations.
- Log external write actions to an audit trail (e.g. `memory/audit.log`).
- If tool state is uncertain, verify before retrying writes.

## MCP tools (OpenClaw & Hermes)

Register **`scripts/pmgo_mcp_server.py`** once per gateway — see [runtimes/README.md](../runtimes/README.md).

- **Read / reports:** `pmgo_project_list`, `pmgo_task_list`, `pmgo_milestone_list`, `pmgo_risk_list`, `pmgo_risk_scan`, `pmgo_decision_list`, `pmgo_daily_report`, `pmgo_weekly_report`, ...
- **Writes (policy may require `confirmed: true` ...):** `pmgo_project_create`, `pmgo_task_create`, `pmgo_task_update`, `pmgo_milestone_create`, `pmgo_milestone_update`, `pmgo_risk_create`, `pmgo_risk_update`, `pmgo_decision_create`, `pmgo_decision_update`, `pmgo_github_sync_tasks`, ...

| Runtime | Register MCP |
| --- | --- |
| OpenClaw | `npm run runtime:config -- --runtime openclaw` → [runtimes/openclaw/README.md](../runtimes/openclaw/README.md) |
| Hermes | `npm run runtime:config -- --runtime hermes` → [runtimes/hermes/README.md](../runtimes/hermes/README.md) |

Reports and `pmgo_risk_scan` use `PMGO_DEFAULT_PROJECT_ID` when `project_id` is omitted.

Runtime checks use `../policy/pmgo.policy.yaml` via `../scripts/pmgo_policy.py`. If a tool returns a message asking to set `confirmed=true`, the user has approved the action in chat—only then re-invoke with `confirmed: true`.
