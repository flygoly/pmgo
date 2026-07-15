# Architecture

`pmgo` is a **runtime-neutral agent persona + MCP skills pack**. Gateways (OpenClaw or Hermes) own channels, cron, and the LLM session; pmgo owns the PM persona, policy-gated tools, and hybrid memory.

## End-to-end flow

```
IM channels (Telegram, Feishu, Slack, …)
        │
        ▼
Gateway (OpenClaw OR Hermes)
        │  persona: agent/*.md
        │  schedules: gateway cron (generated from cron/jobs.yaml)
        ▼
pmgo Agent (lead; specialists = routing guidance + optional multi-agent snippets)
        │
        ▼
stdio MCP: scripts/pmgo_mcp_server.py
   │  policy gate ← policy/pmgo.policy.yaml
   ▼
skills/* Python packages
        │
        ▼
memory/pmgo.db (SQLite)  +  memory/projects/<slug>/*.md
```

## Components

| Layer | Path | Role |
| --- | --- | --- |
| Persona | `agent/` | SOUL, TOOLS, AGENTS, locale overlays |
| MCP hub | `scripts/pmgo_mcp_server.py` | FastMCP stdio tools; every call runs `gate()` |
| Policy | `policy/pmgo.policy.yaml`, `scripts/pmgo_policy.py` | Allow-list, `require_confirm`, quiet hours |
| Skills | `skills/*` | project-core, reports, risk-radar, integrations |
| Memory | `memory/schema.sql`, migrations | Structured entities + Markdown notes |
| Runtimes | `runtimes/{openclaw,hermes}/` | Registration, cron, IM E2E guides |

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
npm run cron:config -- --runtime openclaw
```

Message bodies live in `shared/cron-messages.md`.

## Security

- MCP writes require `confirmed=true` when policy says so.
- CLI scripts are **trusted-operator** paths and do not call `gate()` (see [SECURITY.md](../SECURITY.md)).
- `shell.exec` denied by default; `fs.write` is path-scoped in policy (enforcement when implemented).
- Audit trail for store writes: SQLite `audit_logs` (not `memory/audit.log`).

## Skills / MCP boundary

Skills expose CLIs under `scripts/*.py` and are also wrapped as `pmgo_*` MCP tools. Integrations use stdlib HTTPS clients; secrets come from env (`GITHUB_*`, `LINEAR_*`, `JIRA_*`, …).
