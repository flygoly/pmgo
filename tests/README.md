# Import Validation Tests

This directory contains tests to validate that the current `agent/` package is importable by OpenClaw.

## Test script

- `validate_openclaw_import.sh`

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
