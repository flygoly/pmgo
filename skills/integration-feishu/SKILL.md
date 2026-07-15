# integration-feishu

Feishu (Lark) connector for pmgo: tenant token, tasklist task list/get, and import into local SQLite.

## Status

**M3 scaffold + tasklist import.** The app must be added as a **tasklist member** (viewer+) so `tenant_access_token` can list tasks.

## Environment

| Variable | Required | Purpose |
| --- | --- | --- |
| `FEISHU_APP_ID` | Yes | App ID |
| `FEISHU_APP_SECRET` | Yes | App secret |
| `FEISHU_TASKLIST_GUID` | For `list` | Default tasklist guid |

## CLI

```bash
npm run feishu:smoke
npm run feishu-issues -- list --tasklist-guid <guid>
npm run feishu-issues -- get <task_guid>
npm run feishu-issues -- import-task --project-id <UUID> --task-guid <guid>
```

Import creates a local task with `source=feishu` and `external_id` = Feishu task guid.

## MCP

| Tool | Policy |
| --- | --- |
| `pmgo_feishu_task_list` | `feishu.task.read` |
| `pmgo_feishu_task_get` | `feishu.task.read` |
| `pmgo_feishu_import_task` | `feishu.task.import_task` (`confirmed=true`) |

## Future

- Bitable rows → tasks
- Channel announce via gateway (not direct IM write from MCP)
