# USER - Profile Template

This file defines the user profile structure for session and long-term memory.
Values are runtime-populated; this document specifies fields and defaults.

## Profile Schema

- `name`: display name
- `locale`: `en` | `zh-CN` | `zh-TW`
- `timezone`: IANA timezone, e.g. `Asia/Shanghai`
- `working_hours`: preferred active working window
- `quiet_hours`: do-not-disturb window
- `notification_channels`: preferred channels (telegram/feishu/slack/email)
- `proactive_level`: `low` | `normal` | `high`
- `project_roles`: `{ project_slug: role }`
- `risk_tolerance`: `conservative` | `balanced` | `aggressive`
- `reporting_preference`: granularity and report format preferences

## Team Collaboration Preferences

- `meeting_style`: `async-first` | `sync-heavy`
- `decision_style`: `consensus` | `owner-decides`
- `escalation_rule`: escalation threshold (default blocker > 24h)

## Defaults

- `locale`: `en`
- `timezone`: system timezone
- `proactive_level`: `normal`
- `quiet_hours`: `23:00-08:00`
- `escalation_rule`: `blocked_hours > 24`

## Usage Conventions

- Use defaults when fields are missing and call out assumptions.
- Confirm before persisting preference changes into long-term memory.
- Keep only minimum necessary personal information.
