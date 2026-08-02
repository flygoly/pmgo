# pmgo CLI

The free CLI is the shared automation surface for local use, Hermes, OpenClaw,
and future clients. It requires Python 3.11 or newer.

## Install for development

```bash
python3.11 -m pip install -e .
pmgo onboard --name "My Work" --locale en
```

Without installation, use `npm run pmgo -- <command>` from the repository.

## Local project workflow

```bash
pmgo project list
pmgo project add "Product launch" --use
pmgo task add "Prepare release notes" --priority high
pmgo task list
pmgo task done <task-id>
pmgo context --json
pmgo note show overview
```

`--json` produces stable structured output suitable for agents and shell
automation. Destructive task deletion additionally requires `--yes`.

## Hermes or OpenClaw

Onboarding initializes repository memory, registers the MCP server and persona,
runs diagnostics, and stores the shared database path:

```bash
pmgo onboard --runtime hermes --name "My Work" --open
# or
pmgo onboard --runtime openclaw --name "My Work" --open
```

After onboarding:

```bash
pmgo status
pmgo open
pmgo uninstall --runtime hermes --dry-run
```

Hermes/OpenClaw MCP tools and the CLI use the same `memory/pmgo.db` for a
runtime-connected repository. Standalone mode uses the operating system's pmgo
application-data directory.

## Current command groups

- `onboard`, `status`, `open`, `ui`, `uninstall`
- `project list|add|show|use`
- `task list|add|update|done|delete`
- `context`
- `note list|show|set`

The runtime MCP surface additionally exposes milestones, risks, decisions,
retrospectives, reports, canvases, people, and GitHub, Linear, Jira, Feishu,
and Notion integrations. DingTalk currently has a credential smoke test; task
sync and MCP tools remain planned.
