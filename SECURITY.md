# Security Policy

## Supported Versions

pmgo is in early development. Until v1.0, only the latest released version
on `master` receives security updates. Once we reach v1.0 this table will
expand.

| Version    | Supported          |
| ---------- | ------------------ |
| `master`   | :white_check_mark: |
| pre-v1.0   | :x: (unreleased)   |

## Reporting a Vulnerability

We take the security of pmgo seriously. If you believe you have found a
security vulnerability, please report it to us as described below.

### **Do Not** report security vulnerabilities through public GitHub issues.

Preferred channel: use **GitHub Private Vulnerability Reporting** on this
repository — open the `Security` tab and click `Report a vulnerability`.
This keeps the discussion private until a fix is released.

Alternatively, email the maintainer at **flygoly@gmail.com** with the
subject line prefixed `[pmgo-security]`.

You should receive a response within 48 hours. If for some reason you do
not, please follow up to ensure we received your original message.

### Please include the following information in your report:

- Type of issue (e.g., prompt injection, sandbox escape, credential leak,
  SSRF via a skill connector, unauthorized external tool invocation, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue (LLM provider,
  Gateway version, Skills enabled, IM channel, etc.)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit transcript (if possible)
- Impact of the issue, including how an attacker might exploit it
  (data exfiltration, privileged writes to Jira/GitHub, etc.)

## What to Expect

After you submit a vulnerability report, you can expect the following:

1. **Acknowledgement**: We will acknowledge receipt of your vulnerability report within 48 hours.
2. **Investigation**: We will investigate the issue and determine its severity and impact.
3. **Fix Development**: If accepted, we will work on a fix. This process may take some time depending on the complexity of the issue.
4. **Release**: We will release a security update for all supported versions.
5. **Disclosure**: We will coordinate public disclosure with you. We prefer to fully disclose the issue after a fix is available.

## Security Best Practices

### For Users
- Always use the latest version of pmgo and OpenClaw.
- Review `policy/pmgo.policy.yaml` before running pmgo in a new
  environment — never relax the `shell.exec` or `fs.write` allow-lists
  without understanding the impact.
- Use scoped API tokens for integrations (Jira, GitHub, Linear, Notion,
  Feishu, DingTalk). Prefer read-only tokens where possible.
- Store secrets in `.env` files that are covered by `.gitignore` — never
  commit tokens to the repository.
- Treat messages arriving over IM channels as untrusted input; the Agent
  must not be given tools that let a third party escalate without
  `require_confirm`.

### For Developers
- Follow secure coding practices; validate and normalize every input that
  flows from an LLM response into a tool call.
- Keep TypeScript and Python dependencies up to date (`npm audit`,
  `pip-audit`).
- Run the i18n/lint/test scripts locally before opening a PR.
- Add `require_confirm: true` to any new skill that performs destructive
  or externally visible actions (create/close/delete tickets, post to
  channels, write files outside `memory/`/`reports/`).

## Dependency Security

pmgo uses automated tooling to monitor for vulnerable dependencies:
- Dependabot scans TypeScript and Python manifests for CVEs.
- GitHub Actions include lint, test, and i18n consistency checks.
- All dependencies are reviewed for license compatibility with Apache-2.0.

## License and Legal

This security policy is governed by the same Apache License 2.0 as the
pmgo software. See [LICENSE](LICENSE) for details.