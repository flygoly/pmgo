# daily-standup

Daily project snapshot derived from `memory/pmgo.db` task rows.

## Responsibilities

- Classify tasks into: **done (last 24h)**, **in progress** (`doing`), **up next / tomorrow** (`todo`), **blocked** (`blocked`); `cancelled` is omitted, `done` older than 24h is omitted from the "done" section.
- List **active risks** (`open` / `watching`) with severity.
- Render locale-specific Markdown from `memory/templates/<template>.<locale>.md`.
- Default template: **`daily-report`** (classic daily log). Alternate: `daily-standup`.
- Use `standup.empty` from `locales/<locale>.json` for empty sections.

## Implementation (M1)

- `skills/daily-standup/daily_standup/build.py` — data + template fill
- `scripts/daily-standup.py` — CLI (`npm run daily-report` / `npm run daily-standup`)
- Time basis: **UTC** for the rolling 24h window and the date line.

## CLI

```bash
# Classic daily report (default template)
npm run daily-report -- --project-id <UUID> --locale zh-CN

# Same engine, standup headings
npm run daily-standup -- report --project-id <UUID> --template daily-standup

# Persist under memory/projects/<slug>/daily-reports/YYYY-MM-DD.md
npm run daily-report -- --from-first-project --locale zh-CN --save
```

- `--from-first-project` — pick the first project (smoke: no project → exit 0).
- `--template daily-report|daily-standup` — template basename (default: `daily-report`).
- `--save` — write Markdown into the project memory folder.
- `--db PATH` — override database file.

## MCP

Tool: `pmgo_daily_report` (policy `pmgo.report.daily`). Uses the `daily-report` template by default.
Register via [runtimes/README.md](../../runtimes/README.md).

## Future work

- “Yesterday / today” narrative from audit history or work logs.
