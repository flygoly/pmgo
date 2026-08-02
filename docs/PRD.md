# pmgo Product Requirements Document

**Status:** Active  
**Last updated:** 2026-08-02  
**Primary release target:** Windows, macOS, and Linux desktop

## 1. Product definition

pmgo is an open-source, local-first project-management agent with a commercial
desktop client. The free CLI, MCP server, and agent integrations provide an
open automation surface. The desktop client provides the polished visual,
operational, and operating-system experience that individual users pay for.

The product must work without Hermes or OpenClaw. Those runtimes remain optional
adapters for messaging channels and unattended automation.

## 2. Product principles

1. **Local ownership:** projects, tasks, Markdown, attachments, and agent history
   remain usable without a pmgo cloud account.
2. **One core, multiple surfaces:** Desktop, CLI, and MCP use the same domain
   services and data contract.
3. **Open automation:** CLI, MCP, file formats, import, and export remain open.
4. **Paid experience:** the official desktop client monetizes visual workflows,
   OS integration, and convenience rather than access to user data.
5. **Explicit agency:** tool actions that mutate important state require a
   visible preview, policy evaluation, and confirmation where configured.
6. **Replaceable models:** local and hosted model providers use one adapter
   contract; no project data model depends on a specific LLM vendor.

## 3. Target users

- Individuals managing personal, software, research, or content projects.
- Independent developers using coding agents and local project context.
- Small teams that need structured reports, risks, decisions, and evidence.
- Advanced users integrating pmgo with Hermes, OpenClaw, Codex, scripts, or CI.

## 4. Product surfaces and commercial boundary

| Surface | Distribution | Role |
| --- | --- | --- |
| `pmgo` CLI | Free and open source | Projects, automation, scripting, structured JSON |
| pmgo MCP / Agent | Free and open source | Tool use from compatible agents and runtimes |
| pmgo Desktop | Commercial client | Visual management, native integrations, local agent UX |
| Hosted AI / automation | Optional subscription | Zero-config models, unattended jobs, managed convenience |

The desktop client must never make export, local project access, or recovery of
user-owned data dependent on an active subscription.

## 5. Desktop technology decision

### 5.1 Decision

pmgo will continue with **Electron** for the first commercial Windows, macOS,
and Linux releases.

- Desktop shell: Electron
- Target renderer: React + TypeScript
- Desktop bridge: isolated preload + narrow, typed IPC
- Local core: bundled Python 3.11+ sidecar
- Persistence: SQLite in WAL mode + Markdown + attachment directories
- Packaging: electron-builder, built natively on each target operating system

The current Electron implementation is a foundation, not a throwaway prototype.
The project will not migrate to Tauri merely to reduce bundle size.

### 5.2 Rationale

- pmgo already has an Electron shell, renderer, Python sidecar, packaging config,
  and three-platform CI workflow.
- Bundled Chromium gives complex boards, Markdown, drag-and-drop, charts, and
  streaming agent UI a more consistent rendering target across operating systems.
- Existing JavaScript and web UI skills can reach a commercial-quality product
  faster than introducing Rust or Dart now.
- Agent computation, SQLite work, reports, indexing, and model requests remain
  outside the renderer, so Electron is not the performance-critical core.

### 5.3 Alternatives

**Tauri 2** remains a future optimization option. It offers smaller bundles,
lower baseline resource use, Rust capabilities, sidecars, and cross-platform
updating. It is not selected now because it adds Rust and system-WebView
compatibility work while pmgo must still bundle its Python core.

**Flutter** is not selected for desktop. It would add Dart, replace the existing
web renderer, and require a new integration layer around the Python core. It can
be reconsidered only if sharing one UI implementation with mobile becomes more
valuable than preserving the current desktop/web stack.

Separate native Windows, macOS, and Linux clients are out of scope because their
development and QA cost would slow product validation without improving the
shared agent core.

### 5.4 Reconsideration triggers

The team may evaluate Tauri or a shared Rust core only after all of the following
are true:

1. the paid desktop workflow has been validated with real users;
2. telemetry or support evidence shows Electron memory, startup, or package size
   materially harms activation or retention;
3. the Core API and contract fixtures are stable;
4. a migration prototype passes Windows, macOS, and representative Linux WebView
   compatibility tests;
5. expected maintenance savings exceed the rewrite and dual-stack cost.

## 6. Required architecture

```text
pmgo Desktop Renderer (React + TypeScript)
        │ typed, allow-listed IPC only
        ▼
Electron Main Process
  windows · menus · notifications · secrets · updates · sidecar lifecycle
        │ authenticated local RPC
        ▼
pmgo Core
  projects · reports · personas · scheduler · agent · tools · approvals
        │
        ├── SQLite + Markdown + attachments
        ├── model provider adapters
        └── integration adapters

pmgo CLI ───────────────┐
pmgo MCP Server ────────┴── same Core contract
```

### 6.1 Renderer

The renderer owns presentation only. It must not:

- access Node.js directly;
- read model API keys;
- execute shell commands;
- connect directly to SQLite;
- receive broad filesystem or Electron APIs through preload.

The target UI stack is React + TypeScript with design tokens and a pmgo-owned
component layer. State for server/domain data and transient UI state must remain
separate so model streaming does not force whole-application rerenders.

### 6.2 Electron main process

The main process owns:

- application and window lifecycle;
- native menus, file dialogs, tray, notifications, and global shortcuts;
- OS credential storage;
- updater lifecycle and release-channel selection;
- creation, health checks, restart, and shutdown of the Core sidecar;
- validation of every renderer IPC sender and payload.

### 6.3 pmgo Core

The Core is the product authority and single business-logic boundary. It owns:

- projects, tasks, milestones, risks, decisions, people, and retrospectives;
- daily and weekly report generation and archival;
- configurable project-manager personas and version history;
- scheduler jobs, retries, run history, and delivery state;
- model provider selection and streaming;
- tool registry, policy gate, approval requests, and audit records;
- import, export, backup, restore, migrations, and recovery.

Desktop, CLI, and MCP must converge on this Core instead of implementing domain
rules independently. SQLite writes should be serialized through the Core where
practical; WAL mode supports concurrent readers.

### 6.4 Local communication

The MVP may continue using a random loopback port and a random per-process bearer
token. It must bind only to `127.0.0.1`, disable permissive CORS, limit request
sizes, and terminate with the parent application.

The production hardening target is Unix domain sockets on macOS/Linux and named
pipes on Windows using a versioned JSON-RPC or equivalent typed contract.

## 7. Agent requirements

The desktop client must expose the agent as a working project manager, not only
as a chat window.

### 7.1 Core agent loop

1. receive the user request or scheduled trigger;
2. build a bounded project-context preview;
3. plan tool calls;
4. evaluate policy and request confirmation when required;
5. execute tools through the Core;
6. persist the result and audit trail;
7. stream a concise explanation and next actions to the UI.

### 7.2 Persona configuration

Users can view, draft, validate, preview, activate, version, and roll back the
project-manager persona. Editable behavior includes tone, detail, methodology,
proactivity, reporting preference, and custom working rules.

Persona configuration cannot modify the security policy, bypass confirmation,
grant filesystem access, or enable shell execution.

### 7.3 Scheduled work

The standalone client must eventually schedule and archive daily reports,
weekly reports, risk scans, and reminders without requiring Hermes or OpenClaw.
Each run records its trigger, inputs, output path, delivery result, failure, and
retry state.

## 8. Local data requirements

```text
pmgo-data/
├── pmgo.db
├── projects/<slug>/
│   ├── project-overview.md
│   ├── meetings/
│   ├── decisions/
│   ├── reports/daily/
│   ├── reports/weekly/
│   └── attachments/
├── personas/
├── skills/
├── backups/
└── logs/
```

- SQLite stores structured state, indexes, automation runs, approvals, and
  audit history.
- Markdown stores durable, user-readable narrative material and generated
  reports.
- Original attachments stay local; SQLite stores metadata and content hashes.
- Migrations are versioned and recover safely from an interrupted write.
- Backup and export are available without signing in.

## 9. Model and secret requirements

The first provider contract supports OpenAI-compatible endpoints and Ollama.
Anthropic and Gemini adapters can be added without changing project persistence
or renderer contracts.

- API keys are stored through the operating-system credential mechanism.
- Secrets are never written to SQLite, Markdown, logs, renderer state, or crash
  reports.
- The user sees which project context will be sent before a contextual request.
- BYOK and local models remain available without a hosted pmgo subscription.

## 10. Security requirements

- `nodeIntegration: false`, `contextIsolation: true`, renderer sandbox enabled.
- Packaged local UI only; no privileged remote code.
- Restrictive Content Security Policy and navigation/window allow-lists.
- Typed, narrow preload surface; validate sender and payload for every IPC call.
- Tools declare read/write impact and confirmation requirements.
- Destructive or external side effects display a concrete preview before approval.
- Updates and release artifacts are signed; macOS releases are notarized.
- Logs redact secrets and minimize project content by default.

## 11. Distribution requirements

Each operating system builds on its native CI runner:

- macOS: signed and notarized DMG/ZIP;
- Windows: signed NSIS initially, with MSIX evaluated for store distribution;
- Linux: AppImage and DEB initially, with RPM based on demand.

Windows and macOS support an in-app update path. Linux follows the selected
package channel, with signed update artifacts where supported. Failed updates
must preserve the previous runnable version and user data.

## 12. Delivery phases

### Phase A — Desktop foundation

- replace the prototype renderer with React + TypeScript;
- finalize the typed platform bridge;
- converge CLI/MCP/Desktop project and task operations on the Core;
- implement migrations, backup, recovery, and attachment indexing;
- validate signed three-platform builds.

### Phase B — Agent product

- persona configuration and versioning;
- approval inbox and tool-call timeline;
- built-in daily/weekly scheduler and report archive;
- Anthropic and Gemini providers;
- searchable local project context and Obsidian directory selection.

### Phase C — Commercial readiness

- licensing without data lock-in;
- optional hosted AI and unattended automation;
- crash recovery, support diagnostics, and release channels;
- accessibility, localization, performance, and update acceptance testing;
- paid-client onboarding and conversion measurement.

## 13. Out of scope for the first desktop release

- Rewriting the Python Core in Rust.
- Migrating the desktop shell to Tauri.
- Building separate native UI implementations for each desktop OS.
- Full Android, iOS, or HarmonyOS clients.
- Mandatory pmgo cloud accounts or automatic upload of local project data.
- Real-time multi-user editing.

## 14. Acceptance criteria for the first commercial desktop beta

- One installer works on each supported desktop OS and survives upgrade.
- A user can create, update, export, back up, and restore a project offline.
- Desktop, CLI, and MCP observe the same project/task state.
- An agent can build project context, propose a write, obtain approval, execute
  it, and leave an audit record.
- Daily and weekly reports are generated, archived, and visible in the project.
- Provider keys remain outside project storage and renderer-accessible state.
- A Core crash is detected and recoverable without losing committed data.
- The application can be fully used with BYOK or a local model.

