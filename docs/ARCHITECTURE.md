# Architecture

`pmgo` is a **local-first desktop application with a runtime-neutral core**. The desktop client owns the primary experience and local model session. Gateways (OpenClaw or Hermes) are optional adapters for channels and cron.

## End-to-end flow

```
pmgo Desktop (Windows / macOS / Linux)
        │ isolated IPC
        ▼
local Python sidecar ── model Provider (cloud or local)
        │
        ▼
OS userData/pmgo.db + projects/<slug>/*.md

Optional: OpenClaw / Hermes → stdio MCP → existing skills and policy gate
```

## Components

| Layer | Path | Role |
| --- | --- | --- |
| Desktop | `apps/desktop/` | Electron shell, isolated preload, local UI, OS secret storage |
| App core | `pmgo_app/` | SQLite service, loopback API, model provider boundary |
| Persona | `agent/` | SOUL, TOOLS, AGENTS, locale overlays |
| MCP hub | `scripts/pmgo_mcp_server.py` | FastMCP stdio tools; every call runs `gate()` |
| Policy | `policy/pmgo.policy.yaml`, `scripts/pmgo_policy.py` | Allow-list, `require_confirm`, quiet hours |
| Skills | `skills/*` | project-core, reports, risk-radar, integrations |
| Memory | `memory/schema.sql`, migrations | Structured entities + Markdown notes |
| Runtimes | `runtimes/{openclaw,hermes}/` | Registration, cron, IM E2E guides |

### Internal module boundaries

- `scripts/pmgo_mcp_server.py` is the stable stdio entry point. Tool
  implementations are grouped by domain under `scripts/pmgo_mcp_tools/` and
  register on one shared `FastMCP` instance.
- `project_core.store` is a compatibility facade. Store implementations are
  split into work tracking (`store_work`), governance (`store_governance`),
  collaboration (`store_collaboration`), and shared SQLite helpers
  (`store_base`).

## Memory model

- **Long-term structured:** SQLite tables (`projects`, `tasks`, `milestones`, `risks`, `decisions`, `audit_logs`, …).
- **Long-term narrative:** Markdown under `memory/projects/<slug>/` (overview, decisions, standups).
- **Short-term:** gateway session context only — not stored by pmgo.
- **Roster / retros:** `people` and `retrospectives` have store + MCP/CLI CRUD (see `project-core`).

## Multi-agent topology

Roles (`pmgo`, `planner`, `tracker`, `risker`, `reporter`) are defined in `agent/AGENTS.md`. Runtime wiring is optional: paste snippets from `runtimes/*/multi-agent.snippet.*`. Specialists are not separate packages in this repo.

## Heartbeat / cron

`cron/jobs.yaml` is **intent**, not executed by gateways. Generate CLI commands with:

```bash
npm run cron:config -- --runtime openclaw   # or: hermes
```

Message bodies live in `shared/cron-messages.md`.

## Security

- MCP writes require `confirmed=true` when policy says so.
- CLI scripts are **trusted-operator** paths and do not call `gate()` (see [SECURITY.md](../SECURITY.md)).
- `shell.exec` denied by default; `fs.write` is path-scoped in policy (enforcement when implemented).
- Audit trail for store writes: SQLite `audit_logs` (not `memory/audit.log`).

## Skills / MCP boundary

Skills expose CLIs under `scripts/*.py` and are also wrapped as `pmgo_*` MCP tools. Integrations use stdlib HTTPS clients; secrets come from env (`GITHUB_*`, `LINEAR_*`, `JIRA_*`, …).
