# integration-github

Read and write **GitHub Issues** via REST API v3, and optionally **import** an issue as a pmgo **task** in `memory/pmgo.db` with `source="github"` and `external_id` = the GitHub **numeric issue id** (not the display number), matching the unique index on `(project_id, source, external_id)`.

## Environment

| Variable | Required | Meaning |
| --- | --- | --- |
| `GITHUB_TOKEN` | Yes for API calls | Personal access token (fine-grained or classic) with `repo` / Issues scope for private repos, or `public_repo` for public only |
| `GITHUB_REPO` | Yes for API calls | `owner/name` (exactly one slash), e.g. `flygoly/pmgo` |

Optional: `PMGO_MEMORY_DB` or `--db` for `import-task` (same as other pmgo scripts).

## CLI

Entry: `python3 scripts/github-issues.py` / `npm run github-issues -- …`

| Command | Purpose |
| --- | --- |
| `smoke` | If `GITHUB_TOKEN` and `GITHUB_REPO` are unset, exit 0 (CI-friendly). Otherwise call `/rate_limit` to verify credentials. |
| `list` | List issues (pull requests are excluded). `--state open\|closed\|all` |
| `get <number>` | Fetch one issue by **number** |
| `create` | `--title` and optional `--body` |
| `close <number>` | Set issue state to `closed` |
| `import-task` | `--project-id` and `--number` — creates a local task; fails if the same GitHub id was already imported for that project |

## Idempotency

- Re-running `import-task` for the same issue hits the unique index and exits with an error message (no duplicate row).
- For multi-repo automation, keep one pmgo project per GitHub repo or use separate `project_id` slices so `external_id` namespaces do not collide.

## Safety

- Writes (`create`, `close`, `import-task`) should go through policy + human confirmation when exposed as OpenClaw tools (see `policy/pmgo.policy.yaml`).

## OpenClaw

The same operations are available through the **MCP** server `scripts/pmgo_mcp_server.py` (tools `pmgo_github_*`). Register the server in OpenClaw with `openclaw mcp set` — see `openclaw/README.md`.

## Future work

- Labels, assignees, Projects v2 / linked PRs; two-way sync (push task status to GitHub).
