# Goal Objective Template

Use this template when creating a goal objective after planning or before clearing context.

CP-PUBLISH is required before CP-FINAL unless the user explicitly opts out of commits or PR creation. It creates debt-unit Conventional Commit commits, pushes the branch, and opens a PR whose title is also Conventional Commit formatted. Use the separate `commit skills` skill as the source of truth for commit message and PR title type/scope decisions.

CP-FINAL is an execution checkpoint, not a delegation checkpoint. The agent must run the `run_claude_review.py` command in a shell. Resolve the helper path before writing the objective; do not leave `<skill-dir>` in the final goal. If the transcript shows only a spawned SubAgent, built-in `/review`, or prose review attempt, CP-FINAL has not been attempted.

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
- CP-PUBLISH: Debt-unit commit and PR publication
  - Scope: all verified implementation checkpoints
  - Acceptance: work is committed in debt-unit Conventional Commit commits, branch is pushed, PR is created, and the PR title is Conventional Commit formatted
  - Verification:
    ```bash
    git status --short --branch
    git log <base>..HEAD --oneline
    gh pr view --json title,url,headRefName,baseRefName
    ```
  - Commit/title guidance: use the separate `commit skills` skill for Conventional Commit type/scope selection and formatting
  - Evidence required: final git status, commit list, pushed branch, PR URL, PR title, and PR body path or summary
- CP-FINAL: Acceptance review gate
  - Scope: all completed checkpoints, CP-PUBLISH, and their evidence
  - Acceptance: stdout JSON from the verification command has `status == "ACCEPTED"`
  - Verification (literal command to execute in the shell; do not paraphrase, delegate, or substitute):
    ```bash
    python3 $HOME/.codex/skills/goal-checkpoint-runner/scripts/run_claude_review.py \
      --goal-objective <objective.md> \
      --checkpoints <checkpoints.md> \
      --evidence <evidence.md> \
      --changed-files <changed-files.md> \
      --output review.out
    # Parse stdout JSON; the `status` field MUST be "ACCEPTED" to pass.
    # Exit code mapping: 0 ACCEPTED, 1 CHANGES_REQUESTED, 2 unavailable/UNKNOWN.
    ```
  - Forbidden review paths (do NOT use any of these for CP-FINAL):
    - Spawning internal sub-agents (e.g. Codex `Spawned` / sub-agent review).
    - Built-in `/review` slash command unless the user explicitly asks for it.
    - Self-review by the implementing agent without running the helper above.
    - Treating a SubAgent timeout or missing response as a reviewer result.
  - Evidence required: the exact command invoked, the stdout JSON object, and `review.out` / `<review.out>.prompt.md` paths.

## Completion Rules

- Work one checkpoint at a time.
- Convert CHANGES_REQUESTED review findings into new checkpoints.
- If review fixes are required after PR creation, make additional debt-unit Conventional Commit commits, push them, update the PR as needed, and re-run CP-FINAL.
- Do not call update_goal(status="complete") until every checkpoint is verified, CP-PUBLISH evidence exists, and CP-FINAL is ACCEPTED.
- Preserve unrelated dirty worktree changes; do not revert user work.
```

## Context Reset Handoff

Before clearing context, make sure the next turn can recover:

- The exact checkpoint list.
- User constraints that should not be re-litigated.
- Current status and evidence for each checkpoint.
- Publication evidence: debt-unit commit list, pushed branch, PR URL, PR title, and PR body path or summary.
- Exact `run_claude_review.py` command, stdout JSON, and review output paths.
- Any files intentionally left dirty or out of scope.

If this data is too large for the goal objective, write a repo-local task file only when appropriate for the project, then reference that file path in the objective.
