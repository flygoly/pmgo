# Roadmap

Phased rollout for pmgo. Details stay aligned with root `README.md`.

## M1 — MVP

- Repo scaffold, agent persona, memory bootstrap
- Native skills: `project-core`, `daily-standup`, `weekly-report`
- GitHub Issues connector
- One IM channel E2E (Telegram via OpenClaw) — see `runtimes/openclaw/telegram-e2e.md`
- Personal GTD path: bootstrap → first daily report

**Status:** Core skills and GitHub are in tree; IM E2E docs + onboarding polish are the remaining closure items.

## M2 — Beta

- `risk-radar` (shipped)
- Jira / Linear connectors (read + import shipped; transitions / write-back deepening)
- Live cron/heartbeat via generated gateway commands (`npm run cron:config`)
- Multi-agent config snippets (persona routing + pasteable gateway topology)
- Schema tables `people` / `retrospectives`: **CRUD shipped** (CLI + MCP)
- Linear comment write-back; GitHub `push-done` (local done → close issue)

## M3 — v1.0

- Feishu tasklist list/get/import (shipped); deepen Bitable; DingTalk / Notion deepen
- OpenClaw Live Canvas: Gantt & burndown — see `docs/LIVE_CANVAS.md`
- Publishable skills pack (`SKILL.md` standard) — see `docs/PUBLISHING.md`

Local planning notes (untracked drafts) may live under `docs/plan/`; see `docs/plan/README.md`.
