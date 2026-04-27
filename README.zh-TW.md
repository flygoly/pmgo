# pmgo

> 基於 [OpenClaw](https://github.com/openclaw/openclaw) 打造的 AI 專案經理。

**語言**：[English](./README.md) · [简体中文](./README.zh-CN.md) · **繁體中文**

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
[![Status: early development](https://img.shields.io/badge/status-early--development-orange.svg)](#藍圖)

---

> **提示 — 早期開發階段。** 本專案仍處於初始開發階段，設計、目錄結構與 API 尚未穩定，下方多數技能仍在規劃中而非已交付。**歡迎 Star / Watch 本倉庫，敬請期待** —— 首個 MVP（M1）正在路上。非常歡迎你的回饋與 Issue。

---

## pmgo 是什麼？

`pmgo` 是一個 **OpenClaw Agent 人格 + MCP 技能包**，可以把你的 OpenClaw Gateway 變成一位數位專案經理。一套程式碼涵蓋四類場景：

- 個人 GTD / OKR
- 團隊敏捷（Jira、Linear、GitHub Issues）
- 軟體研發全流程（需求 → 開發 → 測試 → 發佈）
- 通用團隊專案管理（飛書、釘釘、Notion）

它以**技能包形態交付，而非 fork** —— 這樣可以隨官方 OpenClaw 同步升級，不會陷入合併地獄。

## 核心亮點

- **多通道接入**：透過 OpenClaw Gateway 在 Telegram、飛書、Slack、Discord、WhatsApp 等通道與 pmgo 對話。
- **永久在線**：Heartbeat 驅動晨間簡報、阻塞巡查、週五週報，無需手動觸發。
- **持久化記憶**：SQLite + 人類可讀的 Markdown，儲存於 `memory/projects/<slug>/`。
- **權限沙箱**：敏感寫入操作（修改 Jira 狀態、關閉 PR、寫檔案）走白名單策略。
- **多智慧體**：主腦 `pmgo` 分派給 `planner`、`tracker`、`risker`、`reporter` 四個子智慧體。
- **原生國際化**：內建支援英文、簡體中文、繁體中文。

## 快速開始

> 專案目前處於**早期開發階段**，以下指令是目標使用體驗，尚未完全可用。請關注下方藍圖。

```bash
# 先安裝 OpenClaw（見 https://openclaw.ai）
npm i -g openclaw
openclaw onboard

# 新增 pmgo 智慧體（規劃中）
openclaw agent add pmgo
```

## 長期記憶儲存

pmgo 使用混合記憶模型：

- **SQLite 資料庫**（`memory/pmgo.db`）儲存結構化長期實體。
- **Schema SQL**（`memory/schema.sql`）定義標準資料庫結構。
- **Markdown**（`memory/projects/<slug>/`）儲存可讀的專案筆記。

初始化並驗證本地 memory 資料庫：

```bash
npm run memory:check
npm run memory:init
npm run memory:migrate
npm run memory:verify
```

也可以一條指令跑完整個引導流程：

```bash
npm run memory:scaffold
```

如果要同時初始化專案 Markdown 目錄：

```bash
npm run memory:scaffold -- --project-name "PMGO MVP" --locale zh-TW
```

單獨初始化專案級 Markdown 目錄：

```bash
npm run memory:init:project -- --name "PMGO MVP" --locale zh-TW
```

可選參數：

- `--slug`：指定 `memory/projects/` 下的目錄名稱。
- `--locale`：支援 `en`、`zh-CN`、`zh-TW`（預設 `en`）。

## GitHub Issues（選用）

設定 `GITHUB_TOKEN` 與 `GITHUB_REPO=owner/name`（例如 `flygoly/pmgo`），再使用內附的 REST 工具：

```bash
npm run github-issues -- smoke
npm run github-issues -- list --state open
npm run github-issues -- import-task --project-id <UUID> --number 42
```

說明見 `skills/integration-github/SKILL.md`。`import-task` 會建立本機任務，`source=github`，`external_id` 為 GitHub 的數值型 issue id，以便去重。

## Linear（選用）

在 Linear →**設定 → API** 建立 `LINEAR_API_KEY`，然後：

```bash
npm run linear-issues -- smoke
npm run linear-issues -- list --first 10
npm run linear-issues -- get ENG-123
npm run linear-issues -- import-task --project-id <UUID> --identifier ENG-123
```

說明見 `skills/integration-linear/SKILL.md`。`import-task` 使用 `source=linear`，`external_id` 為 Linear 端 issue 的 UUID。

## OpenClaw（工具、通道、排程）

註冊受策略約束的 **MCP 工具服務**（`scripts/pmgo_mcp_server.py`）、連接 **Telegram** 等通道、以 Gateway **cron** 跑日報/週報，請見 **[openclaw/README.md](./openclaw/README.md)**。倉庫根目錄的 `cron/jobs.yaml` 僅為示意；正式排程請用 `openclaw cron add`。

## 架構速覽

```
OpenClaw Gateway（多通道）
        │
        ▼
   pmgo 主腦  ──► planner / tracker / risker / reporter
        │
        ▼
  技能包（MCP）
   project-core · daily-standup · weekly-report · risk-radar
   integration-{github,linear,jira,notion,feishu,dingtalk}
        │
        ▼
   記憶層：SQLite + Markdown   ◄── Heartbeat / Cron 排程任務
```

## 藍圖

| 里程碑 | 範圍 |
|---|---|
| **M1 — MVP**（2–3 週） | 倉庫骨架 · Agent 人格 · 3 個原生技能（`project-core`、`daily-standup`、`weekly-report`）· GitHub Issues 連接器 · 1 個 IM 通道（Telegram 或飛書）· 跑通個人 GTD 端到端 |
| **M2 — Beta**（+3–4 週） | `risk-radar`（Python MCP）· Jira/Linear 連接器 · 多智慧體編排 · 上線 Heartbeat 排程任務 |
| **M3 — v1.0**（+4–6 週） | 飛書/釘釘/Notion 連接器 · 基於 OpenClaw Live Canvas 的甘特圖與燃盡圖 · 依 `SKILL.md` 標準發佈，支援一鍵安裝 |

## 國際化約定

- **程式碼、識別字、commit message、行內註解**：只用英文。
- **README**：以英文為準；`README.zh-CN.md` 與 `README.zh-TW.md` 為鏡像翻譯。
- **使用者可見文案**（Agent 回覆、報告模板、錯誤提示、介面標籤）從 `locales/{en,zh-CN,zh-TW}.json` 載入，依會話使用者的 locale 選擇（回退到 `en`）。
- **Agent 人格檔**：`agent/*.md` 以英文為準；本地化覆蓋版本放在 `agent/locales/{zh-CN,zh-TW}/*.md`。
- **貢獻要求**：新文案先寫英文，再在同一個 PR 裡補上 `zh-CN` 與 `zh-TW` 的翻譯。

## 參與貢獻

歡迎貢獻。幾條基本規則：

1. 程式碼、變數名、函式名、檔名、commit message 使用英文。
2. 新增的使用者可見文案必須在同一個 PR 裡同步三個 locale。
3. 遵守 `policy/pmgo.policy.yaml` 中的白名單策略，不要隨意放開 shell 或刪除權限。

建立 PR 前請執行倉庫檢查（Agent i18n、memory 資源與資料庫驗證、`project-core` 列表冒煙、在有專案時執行 `daily-standup` / `weekly-report` / `risk-radar` 冒煙、未設定 GitHub / Linear 相關環境變數時會略過的 `github-issues:smoke` / `linear-issues:smoke`，以及已安裝 `mcp`/`pyyaml` 時的 `mcp:pmgo:check`）：

```bash
npm run validate
```

完整流程見 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 社群

- [行為準則](./CODE_OF_CONDUCT.md)
- [貢獻指南](./CONTRIBUTING.md)
- [安全策略](./SECURITY.md)

## 授權條款

採用 [Apache License, Version 2.0](./LICENSE) 授權條款。關於署名與再散佈要求，請參閱 [NOTICE](./NOTICE)。
