# integration-dingtalk

DingTalk connector scaffold for pmgo.

## Status

**Planned (M3).** No Python client yet — channel delivery should go through the Hermes/OpenClaw DingTalk plugin when available. Local memory remains SQLite via `project-core`.

## Intended environment (future)

| Variable | Purpose |
| --- | --- |
| `DINGTALK_APP_KEY` | App key |
| `DINGTALK_APP_SECRET` | App secret |

## Near-term workaround

Use Telegram E2E ([runtimes/openclaw/telegram-e2e.md](../../runtimes/openclaw/telegram-e2e.md)) or any gateway channel already configured; pmgo MCP tools are channel-agnostic.
