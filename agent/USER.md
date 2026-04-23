# User Context Contract

This file defines how pmgo stores user-level preferences.

## Expected profile fields

- `name`: display name
- `locale`: `en` | `zh-CN` | `zh-TW`
- `timezone`: IANA timezone string (e.g. `Asia/Shanghai`)
- `working_hours`: preferred time ranges for proactive notifications
- `project_roles`: optional mapping of project to user role

## Defaults

- locale: `en`
- timezone: system timezone
- proactive mode: enabled on weekdays only
