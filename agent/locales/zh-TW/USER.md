# USER 在地化覆蓋（zh-TW）

## 使用者輪廓欄位

- 欄位鍵名維持英文，不翻譯，避免與 schema 偏差。
- 欄位解釋使用繁體中文。

## 團隊協作偏好

- `meeting_style`: `async-first` | `sync-heavy`
- `decision_style`: `consensus` | `owner-decides`
- `escalation_rule`: 阻塞升級門檻

## 預設值

- `locale`: `zh-TW`
- `quiet_hours`: `23:00-08:00`
- `escalation_rule`: `blocked_hours > 24`

## 使用慣例

- 缺失欄位使用預設值並標註假設。
- 偏好變更先確認再寫入長期記憶。

