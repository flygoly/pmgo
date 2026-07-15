# TOOLS 本地化覆蓋（zh-TW）

## 設計原則

- 最小權限、可稽核、可確認、可回滾。

## 預設允許

- 查詢類工具、報告類工具、受路徑約束的記憶讀寫。

## 需確認後執行

- `jira.transition_issue`、`github.close_pr`（策略預留）、GitHub Issues 寫入與同步、批次狀態更新、廣播訊息。

## 預設禁止

- `shell.exec`、未限定路徑寫入、刪除類操作、非冪等同步寫入。

## 冪等與稽核約束

- 以 `external_id` 去重；寫入操作記錄至 SQLite `audit_logs` 表。

## CLI vs MCP

- MCP 走 `gate()`；本地 CLI 為可信操作員路徑，不呼叫策略門禁。

## MCP tools (OpenClaw & Hermes)

- 註冊 `scripts/pmgo_mcp_server.py`；詳見英文主檔與 `runtimes/README.md`。
