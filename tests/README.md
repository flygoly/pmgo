# Import Validation Tests

This directory contains tests to validate that the current `agent/` package is importable by OpenClaw.

## Test script

- `validate_openclaw_import.sh`
- `../scripts/validate-agent-i18n.js`

## What it validates

1. Required OpenClaw agent files exist and are non-empty:
   - `agent/SOUL.md`
   - `agent/IDENTITY.md`
   - `agent/USER.md`
   - `agent/TOOLS.md`
   - `agent/AGENTS.md`
2. Supporting runtime files exist:
   - `policy/pmgo.policy.yaml`
   - `cron/jobs.yaml`
   - `skills/project-core/SKILL.md`
   - `locales/en.json`, `locales/zh-CN.json`, `locales/zh-TW.json`
3. Core i18n key consistency (`agent.greeting`) across locales.
4. Optional real import check using OpenClaw CLI:
   - Modern CLI: `openclaw agents add pmgo-e2e --workspace <repo> --non-interactive --json`
5. Persona i18n coverage for `agent/`:
   - Base files must exist: `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `AGENTS.md`
   - Locale overlays must exist for each supported locale (`zh-CN`, `zh-TW`)

## Usage

Run static checks only (default):

```bash
bash tests/validate_openclaw_import.sh
```

Run static checks + real OpenClaw import E2E:

```bash
OPENCLAW_E2E=1 bash tests/validate_openclaw_import.sh
```

Notes:
- E2E mode requires `openclaw` CLI in `PATH`.
- E2E mode runs with an isolated temporary `HOME` and cleans up after completion.
- The script currently targets the modern OpenClaw CLI (`openclaw agents ...`).

Persona i18n validator usage:

```bash
node scripts/validate-agent-i18n.js
```

Or via package script:

```bash
npm run check:agent-i18n
```

Strict mode validates all of the following for locale overlays:

- Same H2 section count (therefore same section-slot order) as base files
- Minimum meaningful content per section
- No empty H2 section body

Run strict mode:

```bash
npm run check:agent-i18n:strict
```

Run strict mode with JSON output (CI-friendly):

```bash
npm run check:agent-i18n:strict:json
```
