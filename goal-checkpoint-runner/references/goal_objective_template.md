# Goal Objective Template

Use this template when creating a goal objective after planning or before clearing context.

```markdown
# Goal

<One sentence objective. Include the repo/path if relevant.>

## Source Plan

<Paste or summarize the original plan. Keep exact user constraints and named files.>

## Checkpoints

- CP-001: <title>
  - Scope: <files/modules/behavior>
  - Acceptance: <observable done condition>
  - Verification: <commands/manual checks>
  - Evidence required: <what must be recorded>
- CP-002: <title>
  - Scope: ...
  - Acceptance: ...
  - Verification: ...
  - Evidence required: ...
- CP-FINAL: Acceptance review gate
  - Scope: all completed checkpoints and their evidence
  - Acceptance: review output is ACCEPTED
  - Verification: review gate output is classified as accepted
  - Evidence required: reviewer identities or command, review output path/summary

## Completion Rules

- Work one checkpoint at a time.
- Convert CHANGES_REQUESTED review findings into new checkpoints.
- Do not call update_goal(status="complete") until every checkpoint is verified and CP-FINAL is ACCEPTED.
- Preserve unrelated dirty worktree changes; do not revert user work.
```

## Context Reset Handoff

Before clearing context, make sure the next turn can recover:

- The exact checkpoint list.
- User constraints that should not be re-litigated.
- Current status and evidence for each checkpoint.
- Review command or reviewer contract.
- Any files intentionally left dirty or out of scope.

If this data is too large for the goal objective, write a repo-local task file only when appropriate for the project, then reference that file path in the objective.
