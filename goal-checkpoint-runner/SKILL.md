---
name: goal-checkpoint-runner
description: Use when turning a plan into a persistent Codex goal with fine-grained checkpoints, external or multi-agent review gates, ACCEPTED/CHANGES_REQUESTED handling, and evidence-based goal completion. Trigger for goal-mode execution plans, checkpoint decomposition, context-reset handoffs, long-running implementation loops, or final acceptance review gating.
---

# Goal Checkpoint Runner

## Purpose

Use this skill to run long implementation work through Codex goal mode without assuming that goal mode contains a review engine. The skill turns a plan into verifiable checkpoints, preserves the plan across context resets, adds an explicit review gate, and only completes the goal after the gate returns `ACCEPTED`.

## Workflow

1. Capture the source plan before any context clear. If the user has only a rough plan, first split it into checkpoints.
2. Normalize the plan into checkpoint records with stable IDs, acceptance criteria, verification commands, and expected evidence. See `references/checkpoint_schema.md` when the plan needs structure.
3. Build a goal objective that includes the source plan, checkpoint list, final review gate, and completion rules. Use `references/goal_objective_template.md` when composing the objective.
4. Start or continue goal-mode work with that objective. Keep the objective as the source of truth after context reset; if the objective would be too large, write a task file first and reference it from the goal.
5. Work checkpoint by checkpoint. After each checkpoint, record evidence: changed files, tests, manual checks, known residual risk, and whether a review is now required.
6. At the review gate, run `claude -p` through `scripts/run_claude_review.py` by default. If the user provides a different external reviewer command, use that command instead.
7. Treat `CHANGES_REQUESTED` as new checkpoint work. Convert each actionable finding into a checkpoint, fix it, verify it, and re-run the gate.
8. Call `update_goal(status="complete")` only when all checkpoints are done, required evidence exists, and the final review gate is `ACCEPTED`.

## Review Gate Rules

- Do not rely on built-in `/review` as a multi-agent gate unless the user explicitly asks for that exact review path. In Codex 0.131.0, goal persistence and built-in review are separate surfaces.
- Default to `claude -p` for the acceptance review gate. Use `scripts/run_claude_review.py` so the prompt shape, timeout, output path, and acceptance classification stay consistent.
- Treat `claude -p` timeout or empty output as an unavailable review gate, not as acceptance. Do not start fallback reviewers unless the user explicitly asks for a fallback path.
- Require a clear terminal review status: `ACCEPTED` or `CHANGES_REQUESTED`.
- Use `scripts/validate_review_acceptance.py` when a deterministic local check is useful for review output from a file or stdin.
- If a reviewer gives prose without a terminal status, classify it conservatively as `CHANGES_REQUESTED` unless the user confirms acceptance.
- Never mark the goal complete because token budget, time budget, or patience is exhausted.

## Claude Review Shape

The default reviewer is Claude Code in print mode. Use one review prompt that explicitly asks Claude to act as three focused reviewers:

- Implementation reviewer: checks behavior against the checkpoint plan and inspects likely code paths.
- Verification reviewer: checks tests, commands, manual evidence, and missing coverage.
- Scope reviewer: checks unintended changes, user constraints, compatibility/fallback policy, and dirty worktree boundaries.

Give Claude the checkpoint list, changed-file summary, verification evidence, and the required response contract from `references/review_gate.md`. Do not ask Claude to redo implementation.

Keep review inputs compact. Summarize broad diffs into checkpoint evidence and changed-file lists before invoking Claude; pass detailed files only when the review finding depends on them. The helper saves the exact prompt as `<review.out>.prompt.md` by default, so inspect that file when Claude times out or returns an ambiguous result.

## Resources

- `references/checkpoint_schema.md`: Checkpoint format and decomposition rules.
- `references/goal_objective_template.md`: Goal objective template for context-reset handoff.
- `references/review_gate.md`: Review status contract and reviewer prompt skeleton.
- `scripts/run_claude_review.py`: Build and run the default `claude -p` acceptance review.
- `scripts/validate_review_acceptance.py`: Deterministic `ACCEPTED`/`CHANGES_REQUESTED` classifier for review output.
