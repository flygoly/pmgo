# Contributing to pmgo

Thank you for your interest in contributing to pmgo — an AI Project
Manager built as an OpenClaw Agent persona and MCP Skills Pack.

pmgo is in **early development**. APIs, repo layout, and agent behavior
are not yet stable. Early contributions that shape the foundation are
especially valuable.

## Development Setup

pmgo targets the official OpenClaw runtime. Skills are written in
**TypeScript** (native OpenClaw skills) or **Python** (MCP skills).

1. **Install OpenClaw** (once, see https://openclaw.ai).

   ```bash
   npm i -g openclaw
   openclaw onboard
   ```

2. **Clone the repository**

   ```bash
   git clone https://github.com/flygoly/pmgo.git
   cd pmgo
   ```

3. **Install dependencies**

   ```bash
   # TypeScript skills
   npm install        # or pnpm install / bun install

   # Python skills (once per clone)
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e '.[dev]'
   ```

4. **Register pmgo with your local OpenClaw Gateway**

   ```bash
   openclaw agent add ./agent
   ```

5. **Run the test harness**

   ```bash
   npm test
   # Policy tests use PyYAML when available: pip install pyyaml
   pytest
   ```

## Code Style

### General
- Code, identifiers, file names, commit messages, and inline comments
  are **English only**. User-facing strings go through `locales/*.json`.
- Prefer small, focused PRs. One skill or one integration per PR is
  usually the right size.

### TypeScript
- Use the repo's ESLint + Prettier config (`npm run lint`,
  `npm run format`).
- Target Node 20+ and ES2022.
- Keep skills pure where possible; side effects go through the Skill
  context object provided by OpenClaw.

### Python
- Format with `ruff format`; lint with `ruff check`.
- Target Python 3.11+.
- Type-annotate all public functions; `mypy` runs in CI.

### Naming Conventions
- Types / classes: `PascalCase`
- Variables and functions: `camelCase` (TS) / `snake_case` (Python)
- Files: `kebab-case.ts` / `snake_case.py`
- Tests: describe the behavior being tested, not the function name.

## Pull Request Process

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Add or update tests for any new logic.
   - Update `docs/plan/` (local) or root `README*.md` if user-visible
     behavior changes.
   - If you add user-facing strings, update all three locale files
     (`locales/en.json`, `locales/zh-CN.json`, `locales/zh-TW.json`) in
     the same PR — see the Localization section below.

3. **Verify locally**

   ```bash
   npm run validate
   ```

   The same command runs in **GitHub Actions** on every push and pull
   request to `master` (see `.github/workflows/ci.yml`).

   This runs agent i18n checks (`npm run check`), the full memory
   pipeline (`memory:check`, `memory:init`, `memory:migrate`,
   `memory:verify`), a read-only `project-core` list smoke test, and
   `daily-standup` / `weekly-report` / `risk-radar` render smoke tests (no-op when the
   database has no projects), and a GitHub CLI smoke that **skips** when
   `GITHUB_TOKEN` / `GITHUB_REPO` are unset (so CI does not need
   secrets), and `mcp:pmgo:check` (imports `mcp` + `pyyaml` when installed;
   skips otherwise). When TypeScript/Python tooling is wired up, also
   run:

   ```bash
   npm run lint
   npm test
   ruff check .
   pytest
   ```

4. **Commit**
   - Keep commit subjects in imperative mood (`Add X`, `Fix Y`).
   - Follow Conventional Commits where it fits
     (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
   - Do not include `Made-with: Cursor` or similar tool trailers.

   ```bash
   git add .
   git commit -m "feat(skill): add risk-radar severity scoring"
   ```

5. **Push and open a PR**
   - Push to your fork and open a PR against `master`.
   - Fill out the PR template. Describe the user-visible change, the
     motivation, and how you tested it.
   - Link any related issues.

## Testing

- **TypeScript skills**: unit tests live next to the source as
  `*.test.ts` and run with `npm test`.
- **Python skills**: unit tests under `skills/<name>/tests/` run with
  `pytest`.
- **Integration tests** that hit external systems (Jira, GitHub, Feishu)
  must be gated behind env vars and skipped by default; never commit
  real tokens.

## Localization

pmgo supports English, Simplified Chinese, and Traditional Chinese out
of the box. English is the canonical source.

- User-facing keys live in `locales/en.json`; mirrored in
  `locales/zh-CN.json` and `locales/zh-TW.json`.
- Add every new key to **all three** locale files. `scripts/check-i18n.mjs`
  verifies key set equality and ICU placeholder consistency.
- Agent persona files under `agent/*.md` are English; localized overlays
  live under `agent/locales/{zh-CN,zh-TW}/`.
- Report templates under `memory/templates/` are named
  `<kind>.<locale>.md` (e.g. `weekly-report.zh-CN.md`).

If you are not fluent in one of the supported languages, mark the PR as
draft and request a translation in the description — maintainers will
help land the missing locale.

## Documentation

- Update `README.md` (English canonical) for significant changes.
  Mirror the change into `README.zh-CN.md` and `README.zh-TW.md` in the
  same PR, or add `i18n-followup: zh-CN, zh-TW` to the PR description if
  you need help with translation.
- Inline documentation for public APIs and any skill entry point.
- User-facing changes go into `CHANGELOG.md` under `[Unreleased]` once
  that file is introduced.

## License Agreement

By contributing to pmgo, you agree that your contributions will be
licensed under the Apache License, Version 2.0. This is automatic under
Section 5 of the Apache License.

You certify that:
1. The contribution is your original work.
2. You have the right to submit the work under the Apache 2.0 license.
3. The contribution does not violate any third-party rights.

## Questions?

If you have questions about contributing, please:
1. Check existing issues and the local planning docs in `docs/plan/`.
2. Open a new issue for discussion.
3. Contact the maintainer at flygoly@gmail.com.
