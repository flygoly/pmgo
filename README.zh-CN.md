# pmgo

> 面向 [OpenClaw](https://github.com/openclaw/openclaw) 与 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的 AI 项目经理。

**语言**：[English](./README.md) · **简体中文** · [繁體中文](./README.zh-TW.md)

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
[![Status: early development](https://img.shields.io/badge/status-early--development-orange.svg)](#路线图)

---

> **提示 — 早期开发阶段。** 本项目仍处于初始开发阶段，设计、目录结构与 API 尚未稳定，下方多数技能还在规划中而非已交付。**欢迎 Star / Watch 本仓库，敬请期待** —— 首个 MVP（M1）正在路上。非常欢迎你的反馈与 Issue。

---

## pmgo 是什么？

`pmgo` 是一个**运行时无关的 Agent 人格 + MCP 技能包**，可把 OpenClaw 或 Hermes 网关变成数字项目经理。一套代码覆盖四类场景：

- 个人 GTD / OKR
- 团队敏捷（Jira、Linear、GitHub Issues）
- 软件研发全流程（需求 → 开发 → 测试 → 发布）
- 通用团队项目管理（飞书、钉钉、Notion）

它以**技能包形态交付，而非 fork** —— 同一套 MCP 与记忆层可在两种运行时上共用。

## 核心亮点

- **双运行时** — 同时支持 [OpenClaw](https://openclaw.ai) 与 [Hermes](https://github.com/NousResearch/hermes-agent)，见 [runtimes/README.md](./runtimes/README.md)。
- **多渠道接入**：通过网关（OpenClaw 或 Hermes）在 Telegram、飞书、Slack、Discord、WhatsApp 等渠道与 pmgo 对话。
- **永久在线**：Heartbeat 驱动晨间简报、阻塞巡查、周五周报，无需手动触发。
- **持久化记忆**：SQLite + 人类可读的 Markdown，保存在 `memory/projects/<slug>/` 下。
- **权限沙箱**：敏感写操作（修改 Jira 状态、关闭 PR、写文件）走白名单策略。
- **多智能体**：主脑 `pmgo` 分派给 `planner`、`tracker`、`risker`、`reporter` 四个子智能体。
- **原生国际化**：内置支持英文、简体中文、繁体中文。

## 快速开始

> 项目处于**早期开发阶段**。网关相关步骤见 [runtimes/](./runtimes/)。

```bash
npm run gtd:bootstrap -- --name "My GTD" --locale zh-CN
export PMGO_DEFAULT_PROJECT_ID="<uuid>"
export PMGO_WORKSPACE="/absolute/path/to/pmgo"
npm run runtime:config -- --runtime openclaw   # 或 hermes
```

- OpenClaw：[runtimes/openclaw/README.md](./runtimes/openclaw/README.md)
- Hermes：[runtimes/hermes/README.md](./runtimes/hermes/README.md)

## 长期记忆存储

pmgo 使用混合记忆模型：

- **SQLite 数据库**（`memory/pmgo.db`）存储结构化长期实体。
- **Schema SQL**（`memory/schema.sql`）定义标准数据库结构。
- **Markdown**（`memory/projects/<slug>/`）存储可读的项目笔记。

初始化并校验本地 memory 数据库：

```bash
npm run memory:check
npm run memory:init
npm run memory:migrate
npm run memory:verify
```

也可以一条命令跑完整个引导流程：

```bash
npm run memory:scaffold
```

如果要同时初始化项目 Markdown 目录：

```bash
npm run memory:scaffold -- --project-name "PMGO MVP" --locale zh-CN
```

单独初始化项目级 Markdown 目录：

```bash
npm run memory:init:project -- --name "PMGO MVP" --locale zh-CN
```

可选参数：

- `--slug`：指定 `memory/projects/` 下的目录名。
- `--locale`：支持 `en`、`zh-CN`、`zh-TW`（默认 `en`）。

## GitHub Issues（可选）

设置 `GITHUB_TOKEN` 与 `GITHUB_REPO=owner/name`（例如 `flygoly/pmgo`），然后使用仓库自带的 REST 工具：

```bash
npm run github-issues -- smoke
npm run github-issues -- list --state open
npm run github-issues -- import-task --project-id <UUID> --number 42
```

说明见 `skills/integration-github/SKILL.md`。`import-task` 会创建本地任务，`source=github`，`external_id` 为 GitHub 的数值型 issue id，便于去重。

## Linear（可选）

在 Linear →**设置 → API** 创建 `LINEAR_API_KEY`，然后：

```bash
npm run linear-issues -- smoke
npm run linear-issues -- list --first 10
npm run linear-issues -- get ENG-123
npm run linear-issues -- import-task --project-id <UUID> --identifier ENG-123
```

说明见 `skills/integration-linear/SKILL.md`。`import-task` 使用 `source=linear`，`external_id` 为 Linear 侧 issue 的 UUID。

## Jira（可选）

配置 `JIRA_BASE_URL`、`JIRA_EMAIL`、`JIRA_API_TOKEN`（可选 `JIRA_PROJECT` 作为默认 list 的 JQL 项目），然后：

```bash
npm run jira-issues -- smoke
npm run jira-issues -- list --max-results 10
npm run jira-issues -- get PROJ-123
npm run jira-issues -- import-task --project-id <UUID> --issue-key PROJ-123
```

说明见 `skills/integration-jira/SKILL.md`。`import-task` 使用 `source=jira`，`external_id` 为 Jira issue 的数字 id。

## 网关集成（OpenClaw 与 Hermes）

注册 **MCP 工具服务**（`scripts/pmgo_mcp_server.py`）、接入通道、配置定时日报/周报：

| 运行时 | 文档 |
| --- | --- |
| OpenClaw | [runtimes/openclaw/README.md](./runtimes/openclaw/README.md) |
| Hermes | [runtimes/hermes/README.md](./runtimes/hermes/README.md) |
| 总览 | [runtimes/README.md](./runtimes/README.md) |

仓库内 `cron/jobs.yaml` 仅为示意；生产环境请用 `openclaw cron add` 或 `hermes cron create`。

## 架构速览

```
网关（OpenClaw 或 Hermes — 多渠道）
        │
        ▼
   pmgo 主脑  ──► planner / tracker / risker / reporter
        │
        ▼
  技能包（MCP stdio — 共用）
   project-core · daily-standup · weekly-report · risk-radar
   integration-{github,linear,jira,notion,feishu,dingtalk}
        │
        ▼
   记忆层：SQLite + Markdown   ◄── Cron / Heartbeat
```

## 路线图

| 里程碑 | 范围 |
|---|---|
| **M1 — MVP**（2–3 周） | 仓库骨架 · Agent 人格 · 3 个原生技能（`project-core`、`daily-standup`、`weekly-report`）· GitHub Issues 连接器 · 1 个 IM 渠道（Telegram 或飞书）· 跑通个人 GTD 端到端 |
| **M2 — Beta**（+3–4 周） | `risk-radar`（Python MCP）· Jira/Linear 连接器 · 多智能体编排 · 上线 Heartbeat 定时任务 |
| **M3 — v1.0**（+4–6 周） | 飞书/钉钉/Notion 连接器 · 基于 OpenClaw Live Canvas 的甘特图与燃尽图 · 按 `SKILL.md` 标准发布，支持一键安装 |

## 国际化约定

- **代码、标识符、commit message、行内注释**：只用英文。
- **README**：以英文为准；`README.zh-CN.md` 和 `README.zh-TW.md` 为镜像翻译。
- **用户可见文案**（Agent 回复、报告模板、错误提示、界面标签）从 `locales/{en,zh-CN,zh-TW}.json` 加载，按会话用户的 locale 选择（回退到 `en`）。
- **Agent 人格文件**：`agent/*.md` 以英文为准；本地化覆盖版本放在 `agent/locales/{zh-CN,zh-TW}/*.md`。
- **贡献要求**：新文案先写英文，再在同一个 PR 里补上 `zh-CN` 与 `zh-TW` 的翻译。

## 参与贡献

欢迎贡献。几条基本规则：

1. 代码、变量名、函数名、文件名、commit message 使用英文。
2. 新增的用户可见文案必须在同一个 PR 里同步三个 locale。
3. 遵守 `policy/pmgo.policy.yaml` 中的白名单策略，不要随意放开 shell 或删除权限。

提交 PR 前请运行仓库检查（Agent i18n 校验、memory 资源与数据库校验、`project-core` 列表冒烟、在有项目时执行 `daily-standup` / `weekly-report` / `risk-radar` 冒烟、未设置 GitHub / Linear / Jira 相关环境变量时会跳过的 `github-issues:smoke` / `linear-issues:smoke` / `jira-issues:smoke`，以及已安装 `mcp`/`pyyaml` 时的 `mcp:pmgo:check`）：

```bash
npm run validate
```

完整流程见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 社区

- [行为准则](./CODE_OF_CONDUCT.md)
- [贡献指南](./CONTRIBUTING.md)
- [安全策略](./SECURITY.md)

## 许可证

采用 [Apache License, Version 2.0](./LICENSE) 协议。关于署名与再分发要求，请参见 [NOTICE](./NOTICE)。
