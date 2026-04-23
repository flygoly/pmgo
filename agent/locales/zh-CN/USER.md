# USER 本地化覆盖（zh-CN）

## 用户画像字段

- 字段键名保持英文，不翻译，避免与 schema 偏差。
- 字段解释使用简体中文。

## 团队协作偏好

- `meeting_style`: `async-first` | `sync-heavy`
- `decision_style`: `consensus` | `owner-decides`
- `escalation_rule`: 阻塞升级阈值

## 默认值

- `locale`: `zh-CN`
- `quiet_hours`: `23:00-08:00`
- `escalation_rule`: `blocked_hours > 24`

## 使用约定

- 缺失字段使用默认值并标注假设。
- 偏好变化先确认再写入长期记忆。

