# pmgo

> An AI Project Manager for [OpenClaw](https://github.com/openclaw/openclaw) and [Hermes Agent](https://github.com/NousResearch/hermes-agent).

**Languages**: **English** · [简体中文](./README.zh-CN.md) · [繁體中文](./README.zh-TW.md)

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
[![CI](https://github.com/flygoly/pmgo/actions/workflows/ci.yml/badge.svg)](https://github.com/flygoly/pmgo/actions/workflows/ci.yml)
[![Status: early development](https://img.shields.io/badge/status-early--development-orange.svg)](#roadmap)

---

> **Heads up — early development.** This project is still in its initial development phase. The design, repo layout, and APIs are not yet stable, and most skills below are planned rather than shipped. **Star / watch the repo and stay tuned** — a first MVP (M1) is on the way. Feedback and issues are very welcome.

---

## What is pmgo?

`pmgo` is a **runtime-neutral Agent persona + MCP Skills Pack** that turns your OpenClaw or Hermes gateway into a digital project manager. It covers four scenarios with one codebase:

- Personal GTD / OKR
- Agile team workflows (Jira, Linear, GitHub Issues)
- Full software development lifecycle (requirements → dev → test → release)
- General team project management (Feishu, DingTalk, Notion)

It ships as a **skills pack, not a fork** — one MCP server and one memory store work on both runtimes without merge pain.

## Highlights

- **Dual runtime** — same skills on [OpenClaw](https://openclaw.ai) and [Hermes](https://github.com/NousResearch/hermes-agent); see [runtimes/README.md](./runtimes/README.md).
- **Multi-channel** — Telegram, Feishu, Slack, Discord, WhatsApp, and more via your gateway.
- **Always-on** — heartbeats drive morning briefings, blocker scans, and Friday reports without you asking.
- **Persistent memory** — SQLite + human-readable Markdown under `memory/projects/<slug>/`.
- **Sandboxed** — allow-list policy for sensitive writes (Jira transitions, PR close, file writes).
- **Multi-agent** — a main `pmgo` brain delegates to `planner`, `tracker`, `risker`, and `reporter` sub-agents.
- **i18n-ready** — English, Simplified Chinese, and Traditional Chinese out of the box.

## Quick start

> Early development — commands below are the target UX. See [runtimes/](./runtimes/) for gateway-specific steps.

```bash
# 1) Bootstrap local memory + linked project (runtime-agnostic)
npm run gtd:bootstrap -- --name "My GTD" --locale zh-CN
export PMGO_DEFAULT_PROJECT_ID="<uuid-from-output>"
export PMGO_WORKSPACE="/absolute/path/to/pmgo"

# 2) Pick a runtime and register MCP (prints ready-to-run snippet)
npm run runtime:config -- --runtime openclaw   # or: hermes

# 3) OpenClaw: openclaw agent add ./agent
#    Hermes:   hermes claw migrate  OR  copy agent/SOUL.md → ~/.hermes/SOUL.md
```

Guides: [OpenClaw](./runtimes/openclaw/README.md) · [Hermes](./runtimes/hermes/README.md) · [GTD quickstart (OpenClaw)](./runtimes/openclaw/gtd-quickstart.md)

## Repository layout

- `agent/` — persona package (`SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `AGENTS.md`)
- `runtimes/` — OpenClaw and Hermes integration guides
- `shared/` — shared MCP env and cron message templates
- `skills/` - MCP skill definitions and implementations
- `locales/` - runtime i18n dictionaries (`en`, `zh-CN`, `zh-TW`)
- `policy/pmgo.policy.yaml` - allow-list and confirmation policy
- `cron/jobs.yaml` - proactive heartbeat and scheduled jobs
- `memory/templates/` - locale-aware reporting templates
- `memory/schema.sql` - canonical SQLite schema snapshot
- `memory/migrations/` - append-only schema migration history

## Long-term memory storage

pmgo uses a hybrid memory model:

- **SQLite DB** (`memory/pmgo.db`) stores structured long-term entities.
- **Schema SQL** (`memory/schema.sql`) defines canonical database structure.
- **Markdown** (`memory/projects/<slug>/`) stores human-readable project notes.

Initialize and verify local memory DB:

```bash
npm run memory:check
npm run memory:init
npm run memory:migrate
npm run memory:verify
```

Or run the full bootstrap pipeline in one command:

```bash
npm run memory:scaffold
```

And with project markdown scaffolding:

```bash
npm run memory:scaffold -- --project-name "PMGO MVP" --locale zh-CN
```

Initialize project-scoped markdown memory directory:

```bash
npm run memory:init:project -- --name "PMGO MVP" --locale en
```

Optional arguments:

- `--slug` to force a custom directory name under `memory/projects/`.
- `--locale` supports `en`, `zh-CN`, and `zh-TW` (default: `en`).

## GitHub Issues (optional)

Set `GITHUB_TOKEN` and `GITHUB_REPO=owner/name` (for example `flygoly/pmgo`). Then use the bundled REST helper:

```bash
npm run github-issues -- smoke
npm run github-issues -- list --state open
npm run github-issues -- import-task --project-id <UUID> --number 42
```

Details: `skills/integration-github/SKILL.md`. Importing creates a local task with `source=github` and `external_id` set to GitHub’s numeric issue id for idempotency.

## Linear (optional)

Set `LINEAR_API_KEY` from Linear → **Settings → API**. Then:

```bash
npm run linear-issues -- smoke
npm run linear-issues -- list --first 10
npm run linear-issues -- get ENG-123
npm run linear-issues -- import-task --project-id <UUID> --identifier ENG-123
```

Details: `skills/integration-linear/SKILL.md`. Importing sets `source=linear` and `external_id` to Linear’s issue UUID.

## Jira (optional)

Set `JIRA_BASE_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` (optional `JIRA_PROJECT` for default list JQL). Then:

```bash
npm run jira-issues -- smoke
npm run jira-issues -- list --max-results 10
npm run jira-issues -- get PROJ-123
npm run jira-issues -- import-task --project-id <UUID> --issue-key PROJ-123
```

Details: `skills/integration-jira/SKILL.md`. Importing sets `source=jira` and `external_id` to Jira’s numeric issue id.

## Gateway integration (OpenClaw & Hermes)

Register the **policy-aware MCP server** (`scripts/pmgo_mcp_server.py`), connect channels, and schedule daily/weekly runs:

| Runtime | Guide |
| --- | --- |
| **OpenClaw** | [runtimes/openclaw/README.md](./runtimes/openclaw/README.md) |
| **Hermes** | [runtimes/hermes/README.md](./runtimes/hermes/README.md) |
| **Overview** | [runtimes/README.md](./runtimes/README.md) |

The repo `cron/jobs.yaml` is a narrative reference only; use `openclaw cron add` or `hermes cron create` in production.

## Architecture at a glance

```
Gateway (OpenClaw or Hermes — channels)
        │
        ▼
   pmgo Agent  ──► planner / tracker / risker / reporter
        │
        ▼
  Skills Pack (MCP stdio — shared)
   project-core · daily-standup · weekly-report · risk-radar
   integration-{github,linear,jira,notion,feishu,dingtalk}
        │
        ▼
   Memory: SQLite + Markdown   ◄── Cron / heartbeat
```

## Roadmap

| Milestone | Scope |
|---|---|
| **M1 — MVP** (2–3 weeks) | Repo scaffold · agent persona · 3 native skills (`project-core`, `daily-standup`, `weekly-report`) · GitHub Issues connector · 1 IM channel (Telegram or Feishu) · end-to-end personal GTD flow |
| **M2 — Beta** (+3–4 weeks) | `risk-radar` (Python MCP) · Jira/Linear connector · multi-agent orchestration · cron/heartbeat jobs live |
| **M3 — v1.0** (+4–6 weeks) | Feishu/DingTalk/Notion connectors · Gantt & burndown on OpenClaw Live Canvas · publishable `SKILL.md` for one-click install |

## Internationalisation

- **Code, identifiers, commit messages, and inline comments**: English only.
- **README**: English is canonical; `README.zh-CN.md` and `README.zh-TW.md` mirror it.
- **User-facing strings** (agent replies, report templates, error messages, UI labels) are loaded from `locales/{en,zh-CN,zh-TW}.json` and selected per-session based on the user's locale (fallback: `en`).
- **Agent persona files**: `agent/*.md` are English canonical; localised overlays live under `agent/locales/{zh-CN,zh-TW}/*.md`.
- **Contributions**: please write new strings in English first, then add translations for `zh-CN` and `zh-TW` in the same PR.

## Contributing

Contributions are welcome. A few ground rules:

1. Code, variable names, function names, file names, and commit messages are in English.
2. New user-facing strings must be added to all three locale files in the same PR.
3. Follow the allow-list policy in `policy/pmgo.policy.yaml` — never expand shell or delete permissions casually.

Before opening a PR, run the repository checks (agent i18n validation, memory asset and database verification, `project-core` list smoke, `daily-standup` / `weekly-report` / `risk-radar` smokes when a project exists, `github-issues:smoke`, `linear-issues:smoke`, and `jira-issues:smoke` when the respective API env vars are missing, and `mcp:pmgo:check` for OpenClaw MCP dependencies when `pip install mcp pyyaml` is available):

```bash
npm run validate
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full workflow.

## Community

- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Contributing Guide](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)

## License

Licensed under the [Apache License, Version 2.0](./LICENSE). See [NOTICE](./NOTICE) for attribution requirements.
