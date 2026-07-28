# Personal GTD quickstart (pmgo + OpenClaw)

End-to-end: **bootstrap memory → register MCP → import agent → optional Telegram cron**.

Prerequisites: [OpenClaw](https://openclaw.ai) (`npm i -g openclaw`), Python 3.11+, this repo cloned.

Hermes users: see [../hermes/gtd-quickstart.md](../hermes/gtd-quickstart.md) — steps 1 and 4 are identical; only MCP registration and cron differ.

---

## 1) Bootstrap SQLite + Markdown

```bash
npm run gtd:bootstrap -- --name "My GTD" --locale zh-CN
export PMGO_DEFAULT_PROJECT_ID="<uuid-from-output>"
export PMGO_DEFAULT_LOCALE=zh-CN
export PMGO_WORKSPACE="/absolute/path/to/pmgo"
```

---

## 2) Install pmgo into OpenClaw

```bash
npm run setup -- --runtime openclaw
npm run doctor -- --runtime openclaw
```

This registers both the MCP server and the `pmgo` Agent workspace.

---

## 3) Local GTD loop (no Gateway)

```bash
npm run project-core -- task-create --project-id "$PMGO_DEFAULT_PROJECT_ID" --title "Review inbox"
npm run daily-standup -- report
npm run weekly-report -- report
npm run risk-radar -- report
```

---

## 4) Telegram cron (optional)

See [cron.examples.sh](./cron.examples.sh) and [shared/cron-messages.md](../../shared/cron-messages.md).

---

## 5) Verify

```bash
npm run validate
openclaw mcp list
```
