# Publishing the pmgo skills pack

Target M3 deliverable: a versioned, installable skills pack aligned with OpenClaw / Hermes `SKILL.md` conventions.

## Layout checklist

Each skill under `skills/<name>/` should include:

- `SKILL.md` — purpose, env vars, CLI, MCP tool names, policy keys
- Implementation package (`*_integration/` or skill module)
- Optional smoke: `npm run <skill>:smoke` that skips without credentials

Shared MCP hub remains `scripts/pmgo_mcp_server.py` (one registration per workspace).

## Versioning

- Repo version: `package.json` / `pyproject.toml` (`0.1.0` today)
- Tag releases as `vX.Y.Z` when the MCP tool surface is considered stable enough for consumers
- Document breaking tool renames in the release notes

## One-click install (target UX)

```bash
# Illustrative — exact gateway command TBD at M3
openclaw skill install github:flygoly/pmgo
# or
hermes skill add pmgo --from github.com/flygoly/pmgo
```

Until then:

```bash
git clone https://github.com/flygoly/pmgo.git
cd pmgo && npm run gtd:bootstrap -- --name "My GTD"
npm run runtime:config -- --runtime openclaw
```

See [DEPLOY.md](./DEPLOY.md) and [FIRST_DAILY_REPORT.md](./FIRST_DAILY_REPORT.md).
