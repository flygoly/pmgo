# weekly-report

Weekly status Markdown aligned with `memory/templates/weekly-report.<locale>.md`, filled from `memory/pmgo.db`.

## Responsibilities

- **Week boundaries**: current ISO week in **UTC** (Monday 00:00 to Sunday 23:59:59) with optional `--week-offset` (0 = this week, -1 = previous).
- **Tasks**: per-status counts; “completed this week” = `status = done` and `updated_at` in the week window.
- **Milestones**: list title + status (no historical move detection in M1).
- **Risks**: `open` / `watching` rows, severity-ordered.
- **Next actions**: up to two tasks from `todo` + `doing` + `blocked`, sorted by due date then title.
- Evidence placeholders are `—` until integrations supply URLs.

## Implementation (M1)

- `skills/weekly-report/weekly_report/build.py`
- `scripts/weekly-report.py` — CLI (`npm run weekly-report -- …`)

## CLI

```bash
python3 scripts/weekly-report.py report --project-id <UUID> --locale en
npm run weekly-report -- report --project-id <UUID> --locale zh-TW --week-offset 0
```

- `--from-first-project` — smoke / CI; no project → exit 0.
- `--db PATH` — override database file.

## Future work

- Richer “milestones moved this week” when milestone `updated_at` exists; PR/issue evidence fields from GitHub.
