# Checkpoint Schema

Use checkpoints as small, independently verifiable units of work. A checkpoint should be large enough to produce useful progress and small enough that a reviewer can decide whether it is done from evidence.

## Record Format

```yaml
- id: CP-001
  title: Short action-oriented name
  purpose: Why this checkpoint exists
  implementation_scope:
    - Files, modules, commands, or behavior expected to change
  acceptance_criteria:
    - Observable condition that must be true
  verification:
    - Command, test, manual check, or inspection path
  evidence:
    - To be filled while executing: command output, screenshots, file refs, or notes
  dependencies:
    - Prior checkpoint IDs or external prerequisites
  review_notes:
    - Specific risks reviewers should inspect
  status: pending
```

## Decomposition Rules

- Start from user-visible behavior or explicit acceptance criteria, then map to files and verification.
- Prefer 3-8 checkpoints for normal tasks. Use more only when the task crosses modules, contracts, or release boundaries.
- Add `CP-PUBLISH` immediately before the final review gate unless the user explicitly opts out of commits or PR creation. It must verify debt-unit Conventional Commit commits, pushed branch state, PR creation, and a Conventional Commit formatted PR title. Use the separate `commit skills` skill for commit message and PR title formatting decisions.
- During planning, ask the user to select the final quality gate: `SubAgents Review`, `Codex Review`, or `Claude Review`. Prefer `AskUserQuestion` when the host supports it.
- Make the final checkpoint the selected quality gate when acceptance review is required. Record the chosen gate, reviewer paths, parallel execution plan, and merge rule.
- If a checkpoint cannot be verified, split it or add a concrete verification method before starting the goal.
- Do not hide unresolved review findings inside a completed checkpoint. Create follow-up checkpoint IDs for them.

## Status Values

- `pending`: Not started.
- `in_progress`: Current active checkpoint.
- `blocked`: Waiting on user input, external service, dependency, or failed prerequisite.
- `implemented`: Code/docs changed, but verification or review is incomplete.
- `verified`: Local verification evidence exists.
- `accepted`: Final review has accepted the checkpoint or the whole goal.
