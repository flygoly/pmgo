# Contributing to pmgo

Thank you for your interest in contributing to pmgo — an AI Project
Manager built as a runtime-neutral Agent persona and MCP Skills Pack
(OpenClaw and Hermes).

pmgo is in **early development**. APIs, repo layout, and agent behavior
may still change. Early contributions that shape the foundation are
especially valuable.

## Development Setup

Skills and the MCP server are **Python 3.11+**. Node is used only as a
task runner (`package.json` scripts) and for agent i18n validation
(`scripts/validate-agent-i18n.js`). There is no TypeScript skills
toolchain in this repo yet.

1. **Pick a runtime** (or both) — see [runtimes/README.md](./runtimes/README.md).

   **OpenClaw**

   ```bash
   npm i -g openclaw
   openclaw onboard
   ```

   **Hermes** — see https://github.com/NousResearch/hermes-agent

2. **Clone the repository**

   ```bash
   git clone https://github.com/flygoly/pmgo.git
   cd pmgo
   ```

3. **Install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install '.[mcp]'          # mcp + pyyaml for MCP / Hermes snippets
   pip install '.[dev]'          # coverage (optional local)
   ```

4. **Bootstrap memory (optional)**

   ```bash
   npm run gtd:bootstrap -- --name "Dev GTD" --locale en
   ```

5. **Register pmgo with your local gateway**

   ```bash
   npm run runtime:config -- --runtime openclaw
   openclaw agent add ./agent
   ```

6. **Run tests**

   ```bash
   npm test
   npm run validate
   ```

## Code Style

### General

- Code, identifiers, file names, commit messages, and inline comments
  are **English only**. User-facing strings go through `locales/*.json`
  or Markdown templates under `memory/templates/`.
- Prefer small, focused PRs. One skill or one integration per PR is
  usually the right size.

### Python

- Target Python 3.11+.
- Prefer stdlib where practical (`urllib`, `sqlite3`).
- Type-annotate public functions.
- Follow existing `snake_case` module layout under `skills/<name>/`.

### Naming Conventions

- Types / classes: `PascalCase`
- Functions / modules: `snake_case`
- Tests: `tests/test_*.py` describing behavior

## Pull Request Process

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Add or update tests for any new logic.
   - Update `docs/` or root `README*.md` if user-visible behavior changes.
   - If you add user-facing strings, update all three locale files
     (`locales/en.json`, `locales/zh-CN.json`, `locales/zh-TW.json`) in
     the same PR.

3. **Verify locally**

   ```bash
   npm test
   npm run validate
   ```

   The same commands run in **GitHub Actions** on every push and pull
   request to `master` / `main` (see `.github/workflows/ci.yml`).

4. **Commit**
   - Keep commit subjects in imperative mood (`Add X`, `Fix Y`).
   - Follow Conventional Commits where it fits
     (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).

   ```bash
   git add .
   git commit -m "feat(skill): add risk-radar severity scoring"
   ```

5. **Push and open a PR**
   - Push to your fork and open a PR against `master`.
   - Describe the user-visible change, motivation, and how you tested.

## Testing

- **Unit / integration tests** live under `tests/` and run with
  `python3 -m unittest` via `npm test`.
- **MCP tools** are covered in `tests/test_pmgo_mcp_tools.py` (temp DB +
  policy).
- **HTTP clients** use mocked `urllib` responses where possible.
- Tests that hit external systems (Jira, GitHub, Feishu) must be gated
  behind env vars and skipped by default; never commit real tokens.

### CLI vs MCP policy

- **MCP** (`scripts/pmgo_mcp_server.py`) enforces `policy/pmgo.policy.yaml`
  via `gate()`.
- **CLI** scripts under `scripts/*.py` are **trusted-operator** tools for
  local admins and do **not** call `gate()`. Do not expose CLI wrappers
  to untrusted IM users.

## Localization

pmgo supports English, Simplified Chinese, and Traditional Chinese.

- User-facing keys live in `locales/en.json`; mirrored in
  `locales/zh-CN.json` and `locales/zh-TW.json`.
- Agent persona files under `agent/*.md` are English; localized overlays
  live under `agent/locales/{zh-CN,zh-TW}/`.
- Report templates under `memory/templates/` are named
  `<kind>.<locale>.md`.
- Agent overlay consistency: `npm run check:agent-i18n`.

## Documentation

- Update `README.md` (English canonical) for significant changes.
  Mirror into `README.zh-CN.md` and `README.zh-TW.md` in the same PR when
  practical, or note `i18n-followup` in the PR description.
- Architecture / deploy: `docs/ARCHITECTURE.md`, `docs/DEPLOY.md`.
- Local untracked drafts may go under `docs/plan/` (see
  `docs/plan/README.md`).

## License Agreement

By contributing to pmgo, you agree that your contributions will be
licensed under the Apache License, Version 2.0. This is automatic under
Section 5 of the Apache License.

You certify that:
1. The contribution is your original work.
2. You have the right to submit the work under the Apache 2.0 license.
3. The contribution does not violate any third-party rights.

## Questions?

1. Check existing issues and [docs/ROADMAP.md](./docs/ROADMAP.md).
2. Open a new issue for discussion.
3. Contact the maintainer at flygoly@gmail.com.
