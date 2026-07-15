# integration-notion

Notion connector scaffold for pmgo.

## Status

**Scaffold (M3):** Notion API user smoke + CLI. Database → task import is planned.

## Environment

| Variable | Required | Purpose |
| --- | --- | --- |
| `NOTION_TOKEN` | Yes | Internal integration token |

## CLI

```bash
npm run notion:smoke
python3 scripts/notion-issues.py smoke
```

## Future

- Map a Notion database to `tasks` (`source=notion`, `external_id=page id`)
- Two-way status sync (policy-gated)
