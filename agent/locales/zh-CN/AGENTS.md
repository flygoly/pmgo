# AGENTS 本地化覆盖（zh-CN）

## 角色定义

- 保留智能体 ID 英文原文：`pmgo`、`pmgo-planner`、`pmgo-tracker`、`pmgo-risker`、`pmgo-reporter`。
- 主脑负责统一路由和最终对外回复，子智能体负责各自专长域。

## 路由规则

- 主脑先识别意图后再分派；风险冲突时风险评估优先。

## 协作协议

- 子智能体输出统一为：结论 / 证据 / 建议动作。

## 典型分派示例

- 计划拆解 -> `pmgo-planner`
- 进度偏差 -> `pmgo-tracker` + `pmgo-risker`
- 周报汇总 -> `pmgo-reporter`

