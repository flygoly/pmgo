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

## 2) Install pmgo into Hermes

```bash
npm run setup -- --runtime hermes
npm run doctor -- --runtime hermes
```

This registers MCP and merges a managed pmgo persona block into Hermes. Existing
Hermes configuration and persona files are backed up before they change.

---

## 3) Alternative migration from OpenClaw

**From OpenClaw:**

```bash
hermes claw migrate --dry-run
hermes claw migrate
```

Fresh Hermes installations do not need this step; the setup command above installs
the pmgo persona. Use `--no-persona` if you intentionally want MCP tools only.

---

## 4) Local GTD loop (no gateway)

```bash
npm run project-core -- task-create --project-id "$PMGO_DEFAULT_PROJECT_ID" --title "Review inbox"
npm run daily-standup -- report
npm run weekly-report -- report
npm run risk-radar -- report
```

---

## 5) Feishu channel + cron (optional)

Full IM acceptance checklist: [feishu-e2e.md](./feishu-e2e.md).

```bash
hermes gateway setup   # Feishu + websocket
npm run cron:config -- --runtime hermes
```

Shared messages: [shared/cron-messages.md](../../shared/cron-messages.md) · [cron.examples.sh](./cron.examples.sh).

---

## 6) Verify

```bash
npm run validate
# In Feishu / Hermes chat: ask to run pmgo_project_list
```
