# TOOLS - Tool Allowlist Policy

`pmgo` can only use controlled tools. Effective enforcement is defined in `policy/pmgo.policy.yaml`.

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
- `github.issue.create`, `github.issue.update`, and `github.issue.import_task` (Issues REST writes and local task import)
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

## OpenClaw MCP tools (pmgo server)

When the Gateway loads **`scripts/pmgo_mcp_server.py`** (see `../openclaw/README.md`), the agent sees tools such as:

- **Read / reports:** `pmgo_project_list`, `pmgo_task_list`, `pmgo_risk_scan`, `pmgo_daily_report`, `pmgo_weekly_report`, `pmgo_github_issue_list`, `pmgo_github_issue_get`, `pmgo_linear_issue_list`, `pmgo_linear_issue_get`
- **Writes (policy may require `confirmed: true` in the same tool call after user approval):** `pmgo_project_create`, `pmgo_task_create`, `pmgo_github_issue_create`, `pmgo_github_issue_close`, `pmgo_github_import_task`, `pmgo_linear_import_task`

Runtime checks use `../policy/pmgo.policy.yaml` via `../scripts/pmgo_policy.py`. If a tool returns a message asking to set `confirmed=true`, the user has approved the action in chat—only then re-invoke with `confirmed: true`.
