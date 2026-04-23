# AGENTS - Multi-Agent Orchestration

`pmgo` uses a lead-agent plus specialist-agent topology for clarity and reliability.

## Roles

- `pmgo` (lead orchestrator)
  - Responsibilities: routing, conflict arbitration, final response, cross-domain decisions
- `pmgo-planner`
  - Responsibilities: requirement clarification, task decomposition, milestone design, dependency mapping
- `pmgo-tracker`
  - Responsibilities: progress tracking, status sync, drift detection, schedule adjustment suggestions
- `pmgo-risker`
  - Responsibilities: risk detection, blocker scanning, impact assessment, escalation guidance
- `pmgo-reporter`
  - Responsibilities: standup aggregation, weekly reports, stakeholder summaries, retrospectives

## Routing Rules

1. `pmgo` interprets user intent first, then dispatches to one or more specialists.
2. For risk-schedule conflicts, `pmgo-risker` assessments take priority over nominal progress signals.
3. External-facing reporting is aggregated through `pmgo-reporter`.
4. Final user-visible decision narratives are produced by `pmgo`.

## Collaboration Protocol

- Specialist outputs must include: `Conclusion`, `Evidence`, and `Recommended Actions`.
- If specialist conclusions conflict, `pmgo` triggers a second-pass validation and explains trade-offs.
- Share only minimum necessary context across agents to reduce noise.

## Typical Dispatch Examples

- "Break down next week's release plan" -> `pmgo-planner`
- "Why did velocity drop this week?" -> `pmgo-tracker` + `pmgo-risker`
- "Generate this week's executive summary" -> `pmgo-reporter`
- "How should we handle blockers beyond 24h?" -> `pmgo-risker` (then escalate through `pmgo` if needed)
