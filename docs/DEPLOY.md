# Deployment

pmgo does not ship a hosted service. You deploy a **local (or self-hosted) gateway** and register the MCP server against a checked-out workspace.

## Prerequisites

- Python ≥ 3.11
- Node 20+ (task runner / i18n check only)
- OpenClaw **or** Hermes Agent installed
- Optional: `pip install mcp pyyaml` for MCP + Hermes YAML snippets

## Local setup

```bash
git clone https://github.com/flygoly/pmgo.git
cd pmgo
python3 -m venv .venv && source .venv/bin/activate
pip install '.[mcp]'   # mcp + pyyaml

# Bootstrap memory + first project (prints env exports)
npm run gtd:bootstrap -- --name "My GTD" --locale en
# Copy the printed export block into your shell or MCP env

# Register MCP with absolute PMGO_WORKSPACE
npm run runtime:config -- --runtime openclaw   # or hermes
```

Full path to first daily report: [FIRST_DAILY_REPORT.md](./FIRST_DAILY_REPORT.md).

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `PMGO_WORKSPACE` | Yes (MCP) | Absolute path to the pmgo repo |
| `PMGO_DEFAULT_PROJECT_ID` | Recommended | Default project UUID for reports/tools |
| `PMGO_DEFAULT_LOCALE` | No | `en` / `zh-CN` / `zh-TW` |
| `PMGO_MEMORY_DB` | No | Override SQLite path |
| `GITHUB_TOKEN` / `GITHUB_REPO` | Optional | GitHub Issues |
| `LINEAR_API_KEY` | Optional | Linear |
| `JIRA_BASE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` | Optional | Jira Cloud |
| `FEISHU_APP_ID` / `FEISHU_APP_SECRET` | Optional | Feishu (scaffold) |
| `NOTION_TOKEN` | Optional | Notion (scaffold) |

Copy from [`.env.example`](../.env.example) and [`shared/mcp.env.example`](../shared/mcp.env.example). Never commit secrets.

## Gateway onboarding

| Runtime | Steps |
| --- | --- |
| OpenClaw | [runtimes/openclaw/README.md](../runtimes/openclaw/README.md) — MCP + `openclaw agent add ./agent` |
| Hermes | [runtimes/hermes/README.md](../runtimes/hermes/README.md) — merge MCP YAML + persona |

## Cron / production checklist

1. MCP env includes `PMGO_WORKSPACE` and `PMGO_DEFAULT_PROJECT_ID`.
2. Generate schedules: `npm run cron:config -- --runtime openclaw`.
3. IM channel E2E: [runtimes/openclaw/telegram-e2e.md](../runtimes/openclaw/telegram-e2e.md).
4. Review `policy/pmgo.policy.yaml` before enabling write-heavy tools.
5. Rollback: remove MCP registration / cron jobs; SQLite + Markdown remain on disk.

## Automation status

There is no container publish or cloud deploy workflow yet. CI runs tests + `npm run validate` on push/PR (see `.github/workflows/ci.yml`).
