# pmgo

> 面向 Windows、macOS、Linux 的本機優先 AI 專案經理；OpenClaw 與 Hermes 是選用連接器。

**語言**：[English](./README.md) · [简体中文](./README.zh-Hans.md) · **繁體中文**

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
[![CI](https://github.com/flygoly/pmgo/actions/workflows/ci.yml/badge.svg)](https://github.com/flygoly/pmgo/actions/workflows/ci.yml)
[![Status: early development](https://img.shields.io/badge/status-early--development-orange.svg)](#藍圖)

---

> **提示 — 早期開發階段。** 設計與 API 仍可能變動。**倉庫內已交付：** `project-core`、日報/週報、`risk-radar`、GitHub/Linear/Jira 連接器、帶策略門禁的 MCP。**仍在規劃：** 飛書/釘釘/Notion 深化、Live Canvas、更完整的多智慧體執行時接線。歡迎回饋與 Issue。

---

## pmgo 是什麼？

`pmgo` 正在成為一個**獨立、本機優先的桌面專案經理**。SQLite、Markdown 與附件留在你的裝置上；模型能力透過可替換 Provider 接入。OpenClaw 與 Hermes 保留為訊息通道與自動化連接器，但不再是安裝與啟動前提。

- 個人 GTD / OKR
- 團隊敏捷（Jira、Linear、GitHub Issues）
- 軟體研發全流程（需求 → 開發 → 測試 → 發佈）
- 通用團隊專案管理（飛書、釘釘、Notion）

它以**技能包形態交付，而非 fork** —— 同一套 MCP 與記憶層可在兩種執行時上共用。

## 核心亮點

- **原生桌面端**：一套產品涵蓋 Windows、macOS 與 Linux，由 Electron 桌面殼與內建 Python 核心組成。
- **本機優先**：SQLite 與 Markdown 儲存在系統應用程式資料目錄，無需雲端服務。
- **模型可選**：首批支援 OpenAI 相容介面與本機 Ollama；金鑰由作業系統安全儲存保管。
- **選用執行時**：仍可將同一套技能連接至 [OpenClaw](https://openclaw.ai) 與 [Hermes](https://github.com/NousResearch/hermes-agent)。
- **多通道接入**：透過閘道（OpenClaw 或 Hermes）在 Telegram、飛書、Slack、Discord、WhatsApp 等通道與 pmgo 對話。
- **永久在線**：Heartbeat 驅動晨間簡報、阻塞巡查、週五週報，無需手動觸發。
- **持久化記憶**：SQLite + 人類可讀的 Markdown，儲存於 `memory/projects/<slug>/`。
- **權限沙箱**：敏感寫入操作（修改 Jira 狀態、關閉 PR、寫檔案）走白名單策略。
- **多智慧體**：主腦 `pmgo` 分派給 `planner`、`tracker`、`risker`、`reporter` 四個子智慧體。
- **原生國際化**：內建支援英文、簡體中文、繁體中文。

## 快速開始

桌面開發預覽：

```bash
npm install
npm run pmgo -- onboard --name "我的工作" --locale zh-Hant
npm run desktop:dev
```

桌面端首次啟動會自動建立本機資料，不需要安裝 OpenClaw 或 Hermes。三個系統的安裝套件透過[桌面建置工作流程](./.github/workflows/desktop-release.yml)分別原生建置，詳見[桌面架構](./docs/DESKTOP.md)。

選用的無介面／執行時流程：

```bash
# 1）初始化本機記憶與關聯專案（會輸出可複製執行的 export 指令）
npm run gtd:bootstrap -- --name "My GTD" --locale zh-TW
# 複製命令輸出的 export 區塊，或：
export PMGO_WORKSPACE="$(pwd)"
export PMGO_DEFAULT_PROJECT_ID="<輸出中的 uuid>"

# 2）無需閘道，先產生第一份日報
npm run daily-standup -- report

# 3）一條指令完成執行時安裝（依賴、MCP、人格/Agent）
npm run setup -- --runtime openclaw   # 或 hermes

# 4）診斷並啟動執行時 Dashboard
npm run doctor -- --runtime openclaw  # 或 hermes
npm run start -- --runtime openclaw   # 或 hermes

# 安全解除安裝（保留 pmgo 專案資料與 OpenClaw Workspace）
npm run uninstall -- --runtime openclaw  # 或 hermes
```

安裝免費 CLI 後，可以直接使用 `pmgo`：

```bash
python3.11 -m pip install -e .
pmgo project list
pmgo task add "準備週回顧" --priority high
pmgo context --json
```

完整指令參考：[docs/CLI.md](./docs/CLI.md)。

使用 `--dry-run` 可預覽安裝動作而不修改執行時設定。如需手動設定，仍可使用
`npm run runtime:config -- --runtime ...`。Setup 會建立或重用專用的
`.pmgo-venv`，並確保 MCP 註冊使用同一個 Python 直譯器。

- OpenClaw：[runtimes/openclaw/README.md](./runtimes/openclaw/README.md)
- Hermes：[runtimes/hermes/README.md](./runtimes/hermes/README.md)
- Telegram E2E：[runtimes/openclaw/telegram-e2e.md](./runtimes/openclaw/telegram-e2e.md)
- 飛書 E2E：[runtimes/hermes/feishu-e2e.md](./runtimes/hermes/feishu-e2e.md)
- 產品需求文件：[docs/PRD.md](./docs/PRD.md)
- 架構：[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## 倉庫結構

- `apps/desktop/` — 跨平台桌面殼與本機 UI
- `pmgo_app/` — 與 Agent 執行時無關的 SQLite 核心、本機 API 與模型 Provider
- `agent/` — 人格套件（`SOUL.md`、`IDENTITY.md`、`USER.md`、`TOOLS.md`、`AGENTS.md`）
- `runtimes/` — OpenClaw 與 Hermes 整合指南
- `shared/` — 共用 MCP 環境變數與排程訊息範本
- `skills/` — MCP 技能定義與實作
- `locales/` — 執行時國際化字典（`en`、`zh-CN`、`zh-TW`）
- `policy/pmgo.policy.yaml` — 白名單與確認策略
- `cron/jobs.yaml` — 排程意圖（透過 `npm run cron:config` 產生 CLI 指令）
- `docs/` — 架構、部署、首份報告、Live Canvas 與發佈文件
- `memory/templates/` — 多語言報告範本
- `memory/schema.sql` — 標準 SQLite Schema 快照
- `memory/migrations/` — 僅追加的資料庫遷移歷史

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

## Jira（選用）

設定 `JIRA_BASE_URL`、`JIRA_EMAIL`、`JIRA_API_TOKEN`（可選 `JIRA_PROJECT` 作為預設 list 的 JQL 專案），然後：

```bash
npm run jira-issues -- smoke
npm run jira-issues -- list --max-results 10
npm run jira-issues -- get PROJ-123
npm run jira-issues -- import-task --project-id <UUID> --issue-key PROJ-123
```

說明見 `skills/integration-jira/SKILL.md`。`import-task` 使用 `source=jira`，`external_id` 為 Jira issue 的數字 id。

## 閘道整合（OpenClaw 與 Hermes）

註冊 **MCP 工具服務**（`scripts/pmgo_mcp_server.py`）、連接通道、設定定時日報/週報：

| 執行時 | 文件 |
| --- | --- |
| OpenClaw | [runtimes/openclaw/README.md](./runtimes/openclaw/README.md) |
| Hermes | [runtimes/hermes/README.md](./runtimes/hermes/README.md) |
| 總覽 | [runtimes/README.md](./runtimes/README.md) |

從 `cron/jobs.yaml` 產生閘道定時命令：

```bash
npm run cron:config -- --runtime openclaw   # 或 hermes
```

## 架構速覽

```
閘道（OpenClaw 或 Hermes — 多通道）
        │
        ▼
   pmgo 主腦  ──► planner / tracker / risker / reporter
        │
        ▼
  技能包（MCP stdio — 共用）
   project-core · daily-standup · weekly-report · risk-radar
   integration-{github,linear,jira,notion,feishu,dingtalk}
        │
        ▼
   記憶層：SQLite + Markdown   ◄── Cron / Heartbeat
```

## 已交付 vs 規劃

| 狀態 | 技能 / 表面 |
|---|---|
| **已交付** | `project-core`、日報/週報、`risk-radar`、GitHub/Linear/Jira、MCP + 策略 |
| **腳手架 / 規劃** | 飛書/釘釘/Notion、Live Canvas、可一鍵安裝的技能包 |

## 藍圖

| 里程碑 | 範圍 |
|---|---|
| **M1 — MVP** | 骨架 · 人格 · 核心報告 · GitHub · Telegram E2E · GTD → 第一條日報 |
| **M2 — Beta** | `risk-radar` · Jira/Linear · cron 產生器 · 多智慧體片段 · 寫回加深 |
| **M3 — v1.0** | 飛書/釘釘/Notion · OpenClaw Live Canvas · 可發佈 `SKILL.md` 包 |

詳見 [docs/ROADMAP.md](./docs/ROADMAP.md)。

## 國際化約定

- **程式碼、識別字、commit message、行內註解**：只用英文。
- **README**：以英文為準；`README.zh-Hans.md` 與 `README.zh-Hant.md` 為鏡像翻譯。
- **使用者可見文案**（Agent 回覆、報告模板、錯誤提示、介面標籤）從 `locales/{en,zh-CN,zh-TW}.json` 載入，依會話使用者的 locale 選擇（回退到 `en`）。
- **Agent 人格檔**：`agent/*.md` 以英文為準；本地化覆蓋版本放在 `agent/locales/{zh-CN,zh-TW}/*.md`。
- **貢獻要求**：新文案先寫英文，再在同一個 PR 裡補上 `zh-CN` 與 `zh-TW` 的翻譯。

## 參與貢獻

歡迎貢獻。幾條基本規則：

1. 程式碼、變數名、函式名、檔名、commit message 使用英文。
2. 新增的使用者可見文案必須在同一個 PR 裡同步三個 locale。
3. 遵守 `policy/pmgo.policy.yaml` 中的白名單策略，不要隨意放開 shell 或刪除權限。

建立 PR 前請執行倉庫檢查（Agent i18n、memory 資源與資料庫驗證、`project-core` 列表冒煙、在有專案時執行 `daily-standup` / `weekly-report` / `risk-radar` 冒煙、未設定 GitHub / Linear / Jira 相關環境變數時會略過的 `github-issues:smoke` / `linear-issues:smoke` / `jira-issues:smoke`，以及已安裝 `mcp`/`pyyaml` 時的 `mcp:pmgo:check`）：

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
