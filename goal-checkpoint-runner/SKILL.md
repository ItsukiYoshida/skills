---
name: goal-checkpoint-runner
description: Use when turning a plan into a persistent Codex goal with fine-grained checkpoints, a mandatory claude -p acceptance review gate, ACCEPTED/CHANGES_REQUESTED handling, and evidence-based goal completion. Trigger for goal-mode execution plans, checkpoint decomposition, context-reset handoffs, long-running implementation loops, or final acceptance review gating. Do not use Codex sub-agents, multi-agent review, built-in /review, or self-review for the final acceptance gate unless the user explicitly opts in.
---

# Goal Checkpoint Runner

## Purpose

Use this skill to run long implementation work through Codex goal mode without assuming that goal mode contains a review engine. The skill turns a plan into verifiable checkpoints, preserves the plan across context resets, adds an explicit `claude -p` review gate, and only completes the goal after the helper returns `ACCEPTED`.

## Workflow

1. Capture the source plan before any context clear. If the user has only a rough plan, first split it into checkpoints.
2. Normalize the plan into checkpoint records with stable IDs, acceptance criteria, verification commands, and expected evidence. See `references/checkpoint_schema.md` when the plan needs structure.
3. Build a goal objective that includes the source plan, checkpoint list, final review gate, and completion rules. Use `references/goal_objective_template.md` when composing the objective.
4. Start or continue goal-mode work with that objective. Keep the objective as the source of truth after context reset; if the objective would be too large, write a task file first and reference it from the goal.
5. Work checkpoint by checkpoint. After each checkpoint, record evidence: changed files, tests, manual checks, known residual risk, and whether a review is now required.
6. At the review gate, you MUST invoke `scripts/run_claude_review.py` as the literal verification command of CP-FINAL and read its stdout JSON `status` field. Do not delegate the review to any internal sub-agent (e.g. Codex `Spawned` sub-agents), to the built-in `/review` slash command, or to the implementing agent itself. The only acceptable substitute is an explicit external reviewer command provided by the user.
7. Treat `CHANGES_REQUESTED` as new checkpoint work. Convert each actionable finding into a checkpoint, fix it, verify it, and re-run the gate.
8. Call `update_goal(status="complete")` only when all checkpoints are done, required evidence exists, and the final review gate is `ACCEPTED`.

## CP-FINAL Execution Rule

Before using any `spawn_agent`, `followup_task`, `/review`, or prose review path for CP-FINAL, stop and run the helper command instead. The expected transcript must contain a shell command invoking `scripts/run_claude_review.py`; if no such command was attempted, CP-FINAL has not started. A timeout from an internal SubAgent is irrelevant to this skill's review gate and must not be treated as review evidence.

## Review Gate Rules

- Do not rely on built-in `/review`, on Codex internal sub-agent spawning (e.g. `Spawned ...` workers), or on self-review by the implementing agent as the acceptance gate. Codex's sub-agent flow does not enforce the review output contract and has been observed to return policy summaries instead of diff reviews; treat it as out of scope for CP-FINAL unless the user explicitly opts in.
- The acceptance review gate MUST run `scripts/run_claude_review.py` (which wraps `claude -p`). Embed the literal command in CP-FINAL's verification field; do not paraphrase, summarize, or replace it with an inline review. Resolve the helper to an executable path before writing the goal objective; for this user's global install, prefer `$HOME/.codex/skills/goal-checkpoint-runner/scripts/run_claude_review.py`.
- Treat `claude -p` timeout, failure, empty output, or missing binary as an unavailable review gate, not as acceptance or actionable requested changes. Do not start fallback reviewers unless the user explicitly asks for a fallback path.
- Require structured review output with `status: "ACCEPTED"` or `status: "CHANGES_REQUESTED"` and a `findings` array.
- Use `scripts/validate_review_acceptance.py` when a deterministic local check is useful for review output from a file or stdin.
- If a reviewer gives prose without structured status, classify it as `UNKNOWN`; do not treat it as accepted or as actionable requested changes.
- Never mark the goal complete because token budget, time budget, or patience is exhausted.

## Claude Review Shape

The default reviewer is Claude Code in non-interactive print mode. Use one review prompt that explicitly asks Claude to act as three focused reviewers:

- Implementation reviewer: checks behavior against the checkpoint plan and inspects likely code paths.
- Verification reviewer: checks tests, commands, manual evidence, and missing coverage.
- Scope reviewer: checks unintended changes, user constraints, compatibility/fallback policy, and dirty worktree boundaries.

Give Claude the checkpoint list, changed-file summary, verification evidence, and the required response contract from `references/review_gate.md`. Do not ask Claude to redo implementation.

The helper keeps OAuth/subscription login compatible by default. It uses `--output-format json`, a JSON schema, model defaults, default permission mode, read-only review tools, strict MCP config, and a bounded budget. This mode is not fully hermetic: Claude may still read normal settings, hooks, and CLAUDE.md context that apply to the subprocess. Use `--hermetic` only when `ANTHROPIC_API_KEY` or `apiKeyHelper` is available and the user explicitly wants `claude --bare` isolation.

Keep review inputs compact. Summarize broad diffs into checkpoint evidence and changed-file lists before invoking Claude; pass detailed files only when the review finding depends on them. The helper saves the exact prompt as `<review.out>.prompt.md` by default, so inspect that file when Claude times out or returns an ambiguous result.

## Resources

- `references/checkpoint_schema.md`: Checkpoint format and decomposition rules.
- `references/goal_objective_template.md`: Goal objective template for context-reset handoff.
- `references/review_gate.md`: Review status contract and reviewer prompt skeleton.
- `scripts/run_claude_review.py`: Build and run the default `claude -p` acceptance review.
- `scripts/validate_review_acceptance.py`: Deterministic `ACCEPTED`/`CHANGES_REQUESTED` classifier for review output.
