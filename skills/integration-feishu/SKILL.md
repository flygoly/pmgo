# integration-feishu

Feishu (Lark) connector scaffold for pmgo.

## Status

**Scaffold (M3):** tenant access token smoke + CLI. Task/bitable sync is planned.

## Environment

| Variable | Required | Purpose |
| --- | --- | --- |
| `FEISHU_APP_ID` | Yes | App ID from Feishu open platform |
| `FEISHU_APP_SECRET` | Yes | App secret |

## CLI

```bash
npm run feishu:smoke
# or
python3 scripts/feishu-issues.py smoke
```

## MCP

Reserved for a future `pmgo_feishu_*` surface. Until then, use the CLI as a trusted-operator path and Telegram/OpenClaw for chat (see `runtimes/openclaw/telegram-e2e.md`).

## Future

- Import Feishu tasks / bitable rows into `tasks` with `source=feishu`
- Channel announce helpers via gateway (not direct IM write from MCP by default)
