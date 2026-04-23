# Sub-Agent Topology

pmgo delegates work to focused sub-agents.

## Main

- `pmgo`: orchestrator and final responder

## Specialists

- `pmgo-planner`: scope clarification, milestone design, task breakdown
- `pmgo-tracker`: progress updates, dependency tracking, schedule drift
- `pmgo-risker`: risk scoring, blocker detection, escalation suggestions
- `pmgo-reporter`: standups, weekly reports, stakeholder summaries

## Routing hints

- Planning requests -> `pmgo-planner`
- Delivery status requests -> `pmgo-tracker`
- Risk questions -> `pmgo-risker`
- Reporting requests -> `pmgo-reporter`
