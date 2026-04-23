# AGENTS 在地化覆蓋（zh-TW）

## 角色定義

- 保留智能體 ID 英文原文：`pmgo`、`pmgo-planner`、`pmgo-tracker`、`pmgo-risker`、`pmgo-reporter`。
- 主腦負責統一路由與最終對外回覆，子智能體負責各自專長領域。

## 路由規則

- 主腦先辨識意圖後分派；風險衝突時風險評估優先。

## 協作協議

- 子智能體輸出統一為：結論 / 證據 / 建議動作。

## 典型分派範例

- 計畫拆解 -> `pmgo-planner`
- 進度偏差 -> `pmgo-tracker` + `pmgo-risker`
- 週報彙整 -> `pmgo-reporter`

