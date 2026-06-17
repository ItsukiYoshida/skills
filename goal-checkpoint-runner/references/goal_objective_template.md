# Goal Objective Template

Use this template when creating a goal objective after planning or before clearing context.

CP-PUBLISH is required before CP-FINAL unless the user explicitly opts out of commits or PR creation. It creates debt-unit Conventional Commit commits, pushes the branch, and opens a PR whose title is also Conventional Commit formatted. Use the separate `commit skills` skill as the source of truth for commit message and PR title type/scope decisions.

CP-FINAL is an execution checkpoint for the quality gate selected during planning. Before writing this objective, ask the user which gate to use with `AskUserQuestion` when available; otherwise ask the same choice in plain text. The allowed choices are `SubAgents Review`, `Codex Review`, and `Claude Review`. Do not silently switch gates after implementation starts.

The objective must record the selected gate and the exact execution plan. When a gate contains multiple reviewers, run them in parallel when the host/runtime supports parallel execution; otherwise run every required reviewer before merging results and note that parallel execution was unavailable.

```markdown
# Goal

<One sentence objective. Include the repo/path if relevant.>

## Source Plan

<Paste or summarize the original plan. Keep exact user constraints and named files.>

## Quality Gate Selection

- Selected gate: <SubAgents Review | Codex Review | Claude Review>
- Selection evidence: <AskUserQuestion result, or the user's plain-text choice>
- Parallel execution plan:
  - <reviewer path 1>
  - <reviewer path 2, if required>
- Merge rule: any blocking finding means CHANGES_REQUESTED; unavailable/ambiguous required reviewers mean UNKNOWN unless another reviewer clearly requests changes; only all-clear required reviewers can produce ACCEPTED.

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
  - Acceptance: the merged quality gate result has `status == "ACCEPTED"`
  - Verification for `Claude Review`:
    ```bash
    python3 $HOME/.codex/skills/goal-checkpoint-runner/scripts/run_claude_review.py \
      --goal-objective <objective.md> \
      --checkpoints <checkpoints.md> \
      --evidence <evidence.md> \
      --changed-files <changed-files.md> \
      --output review.structured.out
    ```
    In parallel, invoke Claude CLI's official review command and save its output:
    ```bash
    claude -p "/review pr#<number>" > review.official.out
    ```
    Use the PR number or PR URL from CP-PUBLISH evidence. Add concise review instructions to the prompt only when needed.
  - Verification for `Codex Review`:
    ```bash
    codex exec \
      --output-schema $HOME/.codex/skills/goal-checkpoint-runner/references/review_schema.json \
      -o review.structured.out \
      - < review-prompt.md
    ```
    In parallel, invoke the active Codex runtime's official `/review` or non-interactive review entrypoint with the same context. Save its output to `review.official.out`.
  - Verification for `SubAgents Review`:
    ```text
    Spawn/request three independent reviewers in parallel:
    - Implementation reviewer
    - Verification reviewer
    - Scope reviewer
    ```
  - Merge step: normalize every reviewer output into the contract in `references/review_gate.md`, then merge with the rule recorded in Quality Gate Selection.
  - Evidence required: selected gate, exact reviewer commands/prompts, parallel execution evidence or sequential fallback note, raw reviewer output paths, normalized reviewer statuses, and merged review JSON.

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
- Selected quality gate, exact reviewer commands/prompts, normalized reviewer statuses, merged review JSON, and raw output paths.
- Any files intentionally left dirty or out of scope.

If this data is too large for the goal objective, write a repo-local task file only when appropriate for the project, then reference that file path in the objective.
