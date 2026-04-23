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
