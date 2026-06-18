# Runtime integration (OpenClaw & Hermes)

pmgo is a **runtime-neutral** Agent persona + MCP Skills Pack. The same codebase powers both gateways:

| Layer | Shared? | Location |
| --- | --- | --- |
| MCP tool server | Yes | `scripts/pmgo_mcp_server.py` |
| Skills + CLI | Yes | `skills/`, `scripts/*.py` |
| Memory (SQLite + Markdown) | Yes | `memory/` |
| Policy gates | Yes | `policy/pmgo.policy.yaml` (enforced inside MCP) |
| Persona | Yes | `agent/SOUL.md`, `AGENTS.md`, `USER.md`, … |
| Gateway wiring | Per runtime | `runtimes/openclaw/`, `runtimes/hermes/` |

Use **one** `memory/pmgo.db` and **one** MCP server registration per machine unless you intentionally isolate environments.

## Choose a runtime

| Prefer | When |
| --- | --- |
| **[OpenClaw](./openclaw/README.md)** | Mature multi-agent orchestration, ClawHub skills, **Live Canvas** (M3), broad channel matrix you already run on OpenClaw |
| **[Hermes](./hermes/README.md)** | Native **Feishu/Lark** WebSocket, self-improving GEPA loop, simpler single-binary deploy, migrating from OpenClaw via `hermes claw migrate` |
| **Both** | OpenClaw for channels + Canvas; Hermes for learning-heavy workflows — share MCP env and SQLite (see each guide) |

## Quick paths

1. **Bootstrap memory** (runtime-agnostic):

   ```bash
   npm run gtd:bootstrap -- --name "My GTD" --locale zh-CN
   export PMGO_DEFAULT_PROJECT_ID="<uuid-from-output>"
   export PMGO_DEFAULT_LOCALE=zh-CN
   export PMGO_WORKSPACE="/absolute/path/to/pmgo"
   ```

2. **Render MCP config** for your gateway:

   ```bash
   npm run runtime:config -- --runtime openclaw
   npm run runtime:config -- --runtime hermes
   ```

3. **Follow the runtime guide**:
   - OpenClaw: [openclaw/README.md](./openclaw/README.md) · [GTD quickstart](./openclaw/gtd-quickstart.md)
   - Hermes: [hermes/README.md](./hermes/README.md) · [GTD quickstart](./hermes/gtd-quickstart.md)

## Shared assets

- [shared/mcp.env.example](../shared/mcp.env.example) — environment variables for MCP `env` blocks
- [shared/cron-messages.md](../shared/cron-messages.md) — agent prompts reused by OpenClaw cron and Hermes cron

## Platform-specific features (not portable)

| Feature | OpenClaw | Hermes |
| --- | --- | --- |
| Live Canvas / Gantt (M3) | Planned | N/A |
| GEPA self-improving skills | N/A | Built-in |
| `openclaw agent add ./agent` | Yes | Use profile + `hermes claw migrate` |
| `hermes claw migrate` | N/A | Imports OpenClaw MCP + memory |

## Legacy path

The top-level [`openclaw/`](../openclaw/) directory is a **compat alias** that points here. Prefer `runtimes/` for new docs.
