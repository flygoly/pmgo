# Tools Policy Overview

pmgo can only call approved tools. Actual enforcement lives in `policy/pmgo.policy.yaml`.

## Allowed by default

- Read-only retrieval tools (project/task queries)
- Reporting and summarization tools
- Locale/template resolution tools

## Require explicit confirmation

- External state-changing operations
  - Issue transitions
  - PR close/merge
  - Broadcast messages to channels

## Disallowed by default

- Arbitrary shell execution
- Unscoped filesystem writes
- Destructive bulk operations
