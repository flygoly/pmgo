# Personal GTD quickstart (pmgo + Hermes)

End-to-end: **bootstrap memory → register MCP → load persona → optional Feishu cron**.

Prerequisites: [Hermes Agent](https://github.com/NousResearch/hermes-agent), Python 3.11+, this repo cloned.

OpenClaw users: see [../openclaw/gtd-quickstart.md](../openclaw/gtd-quickstart.md) — steps 1 and 4 are identical.

---

## 1) Bootstrap SQLite + Markdown

```bash
npm run gtd:bootstrap -- --name "My GTD" --locale zh-CN
export PMGO_DEFAULT_PROJECT_ID="<uuid-from-output>"
export PMGO_DEFAULT_LOCALE=zh-CN
export PMGO_WORKSPACE="/absolute/path/to/pmgo"
```

---

## 2) Register MCP in Hermes

```bash
pip install -e ".[mcp]"
npm run runtime:config -- --runtime hermes
```

Merge the printed YAML into `~/.hermes/config.yaml` under `mcp_servers.pmgo`, then restart the gateway or open a new session.

---

## 3) Load persona

**From OpenClaw:**

```bash
hermes claw migrate --dry-run
hermes claw migrate
```

**Fresh install:** copy `agent/SOUL.md` → `~/.hermes/SOUL.md`, `agent/AGENTS.md` → workspace `AGENTS.md`, `agent/USER.md` → `~/.hermes/memories/USER.md`.

---

## 4) Local GTD loop (no gateway)

```bash
npm run project-core -- task-create --project-id "$PMGO_DEFAULT_PROJECT_ID" --title "Review inbox"
npm run daily-standup -- report
npm run weekly-report -- report
npm run risk-radar -- report
```

---

## 5) Feishu cron (optional)

```bash
hermes gateway setup   # Feishu + websocket
```

Use messages from [shared/cron-messages.md](../../shared/cron-messages.md) with `hermes cron create` — see [cron.examples.sh](./cron.examples.sh).

---

## 6) Verify

```bash
npm run validate
# In Hermes chat: ask to run pmgo_project_list
```
