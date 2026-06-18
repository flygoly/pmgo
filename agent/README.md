# Agent package (pmgo)

Portable persona documents for **OpenClaw** and **Hermes** (and any MCP-capable gateway).

## Core files

- `SOUL.md`
- `IDENTITY.md`
- `USER.md`
- `TOOLS.md`
- `AGENTS.md`

English base files are canonical; locale overlays live under `locales/<locale>/`.

## Import

| Runtime | Command / action |
| --- | --- |
| **OpenClaw** | `openclaw agent add ./agent` |
| **Hermes (migrate)** | `hermes claw migrate` from an existing OpenClaw workspace |
| **Hermes (fresh)** | Copy `SOUL.md` → `~/.hermes/SOUL.md`, `AGENTS.md` → workspace, `USER.md` → memories |

See [runtimes/README.md](../runtimes/README.md).

## Related assets

- Skills: `../skills/`
- Locale strings: `../locales/`
- Policy: `../policy/pmgo.policy.yaml`
- MCP server: `../scripts/pmgo_mcp_server.py`
- Runtime guides: `../runtimes/openclaw/`, `../runtimes/hermes/`
