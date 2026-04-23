# OpenClaw Agent Package (pmgo)

This directory is the importable agent package for OpenClaw.

## Core files

- `SOUL.md`
- `IDENTITY.md`
- `USER.md`
- `TOOLS.md`
- `AGENTS.md`

These root files are the canonical base persona documents (English-first).

## I18n Layout

- Locale overlays live in `locales/<locale>/`.
- Supported persona locales:
  - `locales/zh-CN/{SOUL,IDENTITY,USER,TOOLS,AGENTS}.md`
  - `locales/zh-TW/{SOUL,IDENTITY,USER,TOOLS,AGENTS}.md`
- Runtime resolution:
  1. Load base file from `agent/<FILE>.md`
  2. If locale overlay exists, apply `agent/locales/<locale>/<FILE>.md`
  3. If overlay is missing, fallback to base file only

## Import into OpenClaw

```bash
openclaw agent add ./agent
```

## Related runtime assets

- Skills: `../skills/`
- Locale strings: `../locales/`
- Policy: `../policy/pmgo.policy.yaml`
- Cron jobs: `../cron/jobs.yaml`
