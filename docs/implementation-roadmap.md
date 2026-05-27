# OrgFlow Implementation Roadmap

## Working Protocol

For each task:

1. Define the exact completion criteria.
2. Inspect the existing implementation.
3. Implement only that task.
4. Run focused checks and the full relevant test suite.
5. Commit and push to `main`.
6. Move to the next task only after the working tree is clean.

## Completed

- Expose automation circuit breaker monitoring.
- Expose AI recovery monitoring.
- Record every automation job in `automation_runs`.
- Log AI automation decisions in `ai_execution_logs`.
- Ensure every AI execution failure gets a failure classification.
- Ensure every retry uses `next_retry_at`.
- Ensure every dead-letter stays stored and does not return to execution.
- Build full Automation Health Dashboard.

## Current Track: Automation Hardening

### Next

- Build AI Execution Logs Dashboard.

### Upcoming

- Build Dead-Letter Dashboard.
- Build Circuit Breaker Dashboard.

## Definition Of Done

A task is done only when:

- Code is implemented.
- Tests or verification commands pass.
- The result is committed.
- The result is pushed to GitHub.
- `git status --short` is clean.
