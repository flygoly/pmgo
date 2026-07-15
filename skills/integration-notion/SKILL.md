# integration-notion

Notion connector for pmgo: users/me smoke, database query, page get, and import into local SQLite.

## Environment

| Variable | Required | Purpose |
| --- | --- | --- |
| `NOTION_TOKEN` | Yes | Internal integration token |
| `NOTION_DATABASE_ID` | For `list` | Default database id (share DB with the integration) |

## CLI

```bash
npm run notion:smoke
npm run notion-issues -- list --database-id <id>
npm run notion-issues -- get <page_id>
npm run notion-issues -- import-task --project-id <UUID> --page-id <id>
```

Import sets `source=notion` and `external_id` = page id without dashes.

## MCP

| Tool | Policy |
| --- | --- |
| `pmgo_notion_page_list` | `notion.page.read` |
| `pmgo_notion_page_get` | `notion.page.read` |
| `pmgo_notion_import_task` | `notion.page.import_task` (`confirmed=true`) |

## Future

- Property mapping config (title/status column names)
- Two-way status sync
