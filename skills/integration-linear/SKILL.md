# integration-linear

Read **Linear issues** via the public **GraphQL** API and optionally **import** an issue as a pmgo **task** in `memory/pmgo.db` with `source="linear"` and `external_id` = Linear’s issue **UUID** (unique with `project_id` + `source`).

## Environment

| Variable | Required | Meaning |
| --- | --- | --- |
| `LINEAR_API_KEY` | Yes for API calls | Personal API key from Linear → **Settings → API** |

Optional: `PMGO_MEMORY_DB` or `--db` for `import-task` (same as other pmgo scripts).

## CLI

Entry: `python3 scripts/linear-issues.py` / `npm run linear-issues -- …`

| Command | Purpose |
| --- | --- |
| `smoke` | If `LINEAR_API_KEY` is unset, exit 0 (CI-friendly). Otherwise query `viewer` to verify the key. |
| `list` | Recent issues (`--first` page size, default 20). |
| `get <identifier>` | One issue by **UUID** or human id (e.g. `ENG-42`). |
| `import-task` | `--project-id` and `--identifier` — creates a local task; fails if the same Linear id was already imported for that project |
| `comment` | `<identifier> --body` — post a comment (trusted CLI write) |

## Idempotency

- `external_id` is Linear’s issue `id` (UUID). Re-importing the same issue hits the unique index and exits with an error (no duplicate row).

## Safety

- `import-task` / `pmgo_linear_import_task` and `comment` / `pmgo_linear_comment` require **policy** + `confirmed: true` when configured.

## OpenClaw

MCP tools: `pmgo_linear_issue_list`, `pmgo_linear_issue_get`, `pmgo_linear_import_task`, `pmgo_linear_comment` via `scripts/pmgo_mcp_server.py` — see `runtimes/README.md`.

## Future work

- Create/update issue mutations; project/team-scoped list filters; status write-back.
