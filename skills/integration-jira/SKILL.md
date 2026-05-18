# integration-jira

Read **Jira Cloud issues** via REST API v3 and optionally **import** an issue as a pmgo **task** in `memory/pmgo.db` with `source="jira"` and `external_id` = Jira’s numeric issue **id** (unique with `project_id` + `source`).

## Environment

| Variable | Required | Meaning |
| --- | --- | --- |
| `JIRA_BASE_URL` | Yes | Site URL, e.g. `https://your-domain.atlassian.net` (no trailing slash) |
| `JIRA_EMAIL` | Yes | Atlassian account email for API token auth |
| `JIRA_API_TOKEN` | Yes | API token from [Atlassian account security](https://id.atlassian.com/manage-profile/security/api-tokens) |
| `JIRA_PROJECT` | No | Default project key for `list` when `--jql` is omitted |

Optional: `PMGO_MEMORY_DB` or `--db` for `import-task` (same as other pmgo scripts).

## CLI

Entry: `python3 scripts/jira-issues.py` / `npm run jira-issues -- …`

| Command | Purpose |
| --- | --- |
| `smoke` | If Jira env vars are unset, exit 0 (CI-friendly). Otherwise call `/rest/api/3/myself`. |
| `list` | Search issues (`--jql`, `--max-results`; default JQL uses `JIRA_PROJECT` or `ORDER BY updated DESC`). |
| `get <KEY>` | One issue by key (e.g. `PROJ-123`). |
| `import-task` | `--project-id` and `--issue-key` — creates a local task; fails on duplicate import |

## Status mapping

Jira `statusCategory.key` maps to pmgo task status: `done` → `done`, `indeterminate` → `doing`, status name containing “cancel” → `cancelled`, else `todo`.

## Idempotency

- `external_id` is Jira’s issue `id`. Re-importing hits the unique index and exits with an error.

## Safety

- `import-task` and MCP `pmgo_jira_import_task` require policy + `confirmed: true` when configured (see `policy/pmgo.policy.yaml`).
- `jira.transition_issue` is reserved for future write/transition support.

## OpenClaw

MCP tools: `pmgo_jira_issue_list`, `pmgo_jira_issue_get`, `pmgo_jira_import_task` via `scripts/pmgo_mcp_server.py` — see `openclaw/README.md`.

## Future work

- Issue transitions (`jira.transition_issue`); create/update issue; project-scoped filters; webhook sync.
