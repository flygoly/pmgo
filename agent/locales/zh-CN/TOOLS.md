# TOOLS 本地化覆盖（zh-CN）

## 设计原则

- 最小权限、可审计、可确认、可回滚。

## 默认允许

- 查询类工具、报告类工具、受路径约束的记忆读写。

## 需确认后执行

- `jira.transition_issue`、`github.close_pr`（策略预留）、GitHub Issues 写入与同步、批量状态更新、广播消息。

## 默认禁止

- `shell.exec`、未限定路径写入、删除类操作、非幂等同步写入。

## 幂等与审计约束

- 以 `external_id` 去重；写操作记入 SQLite `audit_logs` 表。

## CLI vs MCP

- MCP 走 `gate()`；本地 CLI 为可信操作员路径，不调用策略门禁。

## MCP tools (OpenClaw & Hermes)

- 注册 `scripts/pmgo_mcp_server.py`；详见英文主文件与 `runtimes/README.md`。
