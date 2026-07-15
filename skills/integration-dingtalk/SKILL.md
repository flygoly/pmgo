# integration-dingtalk

DingTalk connector scaffold for pmgo.

## Status

**Scaffold:** access token smoke CLI. Task/todo sync is planned. Channel delivery should prefer the Hermes/OpenClaw DingTalk plugin.

## Environment

| Variable | Required | Purpose |
| --- | --- | --- |
| `DINGTALK_APP_KEY` | For smoke | App key |
| `DINGTALK_APP_SECRET` | For smoke | App secret |

## CLI

```bash
npm run dingtalk:smoke
# or
python3 scripts/dingtalk-issues.py smoke
```

## Near-term workaround

Use Telegram E2E ([runtimes/openclaw/telegram-e2e.md](../../runtimes/openclaw/telegram-e2e.md)) or any gateway channel; pmgo MCP tools are channel-agnostic.

## Future

- Todo / calendar task list + import (`source=dingtalk`)
- MCP `pmgo_dingtalk_*` surface
