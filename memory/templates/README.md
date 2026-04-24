# Memory Markdown Templates

This directory contains locale-aware long-term memory templates used by pmgo.

## Template Groups

- `project-overview.*.md`: project charter and ongoing context snapshot.
- `meeting-notes.*.md`: structured meeting records and action items.
- `decision-log.*.md`: ADR-like decision history with rationale and evidence.
- `weekly-report.*.md`: periodic project status, risks, and next actions.

## Locales

- `en`: English
- `zh-CN`: Simplified Chinese
- `zh-TW`: Traditional Chinese

## Placeholder Convention

Templates use double braces, for example `{{project_name}}`.
Renderers should replace all placeholders before publishing messages or storing final memory notes.
