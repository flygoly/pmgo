# pmgo

> An AI Project Manager built on [OpenClaw](https://github.com/openclaw/openclaw).

**Languages**: **English** · [简体中文](./README.zh-CN.md) · [繁體中文](./README.zh-TW.md)

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
[![Status: early development](https://img.shields.io/badge/status-early--development-orange.svg)](#roadmap)

---

> **Heads up — early development.** This project is still in its initial development phase. The design, repo layout, and APIs are not yet stable, and most skills below are planned rather than shipped. **Star / watch the repo and stay tuned** — a first MVP (M1) is on the way. Feedback and issues are very welcome.

---

## What is pmgo?

`pmgo` is an **OpenClaw Agent persona + MCP Skills Pack** that turns your OpenClaw gateway into a digital project manager. It covers four scenarios with one codebase:

- Personal GTD / OKR
- Agile team workflows (Jira, Linear, GitHub Issues)
- Full software development lifecycle (requirements → dev → test → release)
- General team project management (Feishu, DingTalk, Notion)

It ships as a **skills pack, not a fork** — so it keeps pace with OpenClaw upstream without merge pain.

## Highlights

- **Multi-channel** — reach pmgo over Telegram, Feishu, Slack, Discord, WhatsApp, and more via the OpenClaw Gateway.
- **Always-on** — heartbeats drive morning briefings, blocker scans, and Friday reports without you asking.
- **Persistent memory** — SQLite + human-readable Markdown under `memory/projects/<slug>/`.
- **Sandboxed** — allow-list policy for sensitive writes (Jira transitions, PR close, file writes).
- **Multi-agent** — a main `pmgo` brain delegates to `planner`, `tracker`, `risker`, and `reporter` sub-agents.
- **i18n-ready** — English, Simplified Chinese, and Traditional Chinese out of the box.

## Quick start

> The project is in **early development** — the commands below are the target UX, not a fully working install yet. Follow the roadmap below for progress.

```bash
# Install OpenClaw first (see https://openclaw.ai)
npm i -g openclaw
openclaw onboard

# Add pmgo as an agent (planned)
openclaw agent add ./agent
```

## OpenClaw Standard Layout

This repository now includes an importable OpenClaw agent package:

- `agent/` - canonical agent package (`SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `AGENTS.md`)
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

## Architecture at a glance

```
OpenClaw Gateway (channels)
        │
        ▼
   pmgo Agent  ──► planner / tracker / risker / reporter
        │
        ▼
  Skills Pack (MCP)
   project-core · daily-standup · weekly-report · risk-radar
   integration-{github,jira,linear,notion,feishu,dingtalk}
        │
        ▼
   Memory: SQLite + Markdown   ◄── Heartbeat/Cron jobs
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

## Community

- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Contributing Guide](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)

## License

Licensed under the [Apache License, Version 2.0](./LICENSE). See [NOTICE](./NOTICE) for attribution requirements.
