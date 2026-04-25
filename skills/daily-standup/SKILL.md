# daily-standup

Daily project snapshot derived from `memory/pmgo.db` task rows (standup-style sections).

## Responsibilities

- Classify tasks into: **done (last 24h)**, **in progress** (`doing`), **up next** (`todo`), **blocked** (`blocked`); `cancelled` is omitted, `done` older than 24h is omitted from the "done" section.
- Render locale-specific Markdown using `memory/templates/daily-standup.<locale>.md`.
- Use `standup.empty` from `locales/<locale>.json` for empty sections.

## Implementation (M1)

- `skills/daily-standup/daily_standup/build.py` — data + template fill
- `scripts/daily-standup.py` — CLI (`npm run daily-standup -- …`)
- Time basis: **UTC** for the rolling 24h window and the date line.

## CLI

```bash
python3 scripts/daily-standup.py report --project-id <UUID> --locale en
# or
npm run daily-standup -- report --project-id <UUID> --locale zh-CN
```

- `--from-first-project` — pick the first project (used for `daily-standup:smoke` / CI; no project → exit 0).
- `--db PATH` — override database file.

## Future work

- OpenClaw / MCP tool surface; “yesterday / today” narrative from audit history or work logs.
