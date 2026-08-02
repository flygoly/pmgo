# Roadmap

Phased rollout for pmgo. Details stay aligned with root `README.md`.

## Desktop foundation — in progress

- Cross-platform Electron shell and local Python sidecar: **scaffold shipped**
- Runtime-independent local SQLite + Markdown initialization: **shipped**
- Task dashboard, board, risk view, AI assistant, provider settings: **MVP shipped**
- OpenAI-compatible and local Ollama provider boundary: **shipped**
- Native DMG/ZIP, NSIS/portable, AppImage/DEB build workflow: **shipped; release artifacts pending CI validation**
- Next: Obsidian vault picker, attachment index, Anthropic/Gemini adapters, auto-update/signing

## Mobile expansion — after desktop stability

- Reuse the responsive client through a platform bridge on Android and iOS
- Add a HarmonyOS shell with the same project contract
- Prioritize capture, review, notifications, and offline reading on mobile
- Design optional end-to-end encrypted sync separately from the local-first core

## M1 — MVP

- Repo scaffold, agent persona, memory bootstrap
- Native skills: `project-core`, `daily-standup`, `weekly-report`
- GitHub Issues connector
- One IM channel E2E (Telegram via OpenClaw) — see `runtimes/openclaw/telegram-e2e.md`
- Hermes Feishu / Lark E2E checklist — see `runtimes/hermes/feishu-e2e.md`
- Personal GTD path: bootstrap → first daily report

**Status:** Core skills and GitHub are in tree; IM E2E checklists exist for OpenClaw Telegram and Hermes Feishu.

## M2 — Beta

- `risk-radar` (shipped)
- Jira / Linear connectors (read + import shipped; transitions / write-back deepening)
- Live cron/heartbeat via generated gateway commands (`npm run cron:config`)
- Multi-agent config snippets (persona routing + pasteable gateway topology)
- Schema tables `people` / `retrospectives`: **CRUD shipped** (CLI + MCP)
- Linear comment write-back; GitHub `push-done` (local done → close issue)

## M3 — v1.0

- Feishu tasklist list/get/import (shipped); deepen Bitable
- Notion database query / import (shipped); DingTalk token smoke (shipped)
- OpenClaw Live Canvas **data export** shipped (`npm run canvas`) — UI rendering still OpenClaw-side
- Publishable skills pack (`SKILL.md` standard) — see `docs/PUBLISHING.md`

Local planning notes (untracked drafts) may live under `docs/plan/`; see `docs/plan/README.md`.
