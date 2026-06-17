---
name: goal-checkpoint-runner
description: Use when turning a plan into a persistent agent goal with fine-grained checkpoints, debt-unit Conventional Commit publication, mandatory PR creation, selectable quality gates, ACCEPTED/CHANGES_REQUESTED handling, and evidence-based goal completion. Trigger for goal-mode execution plans, checkpoint decomposition, context-reset handoffs, long-running implementation loops, debt-unit commit/PR publication, or final acceptance review gating. During planning, ask the user to choose SubAgents Review, Codex Review, or Claude Review as the CP-FINAL quality gate.
---

# Goal Checkpoint Runner

## Purpose

Use this skill to run long implementation work through a persistent agent goal without assuming the host agent contains a reliable review engine. The skill turns a plan into verifiable checkpoints, preserves the plan across context resets, requires debt-unit Conventional Commit publication and PR creation, asks which quality gate to use, and only completes the goal after the selected gate returns `ACCEPTED`.

## Workflow

1. Capture the source plan before any context clear. If the user has only a rough plan, first split it into checkpoints.
2. Normalize the plan into checkpoint records with stable IDs, acceptance criteria, verification commands, and expected evidence. See `references/checkpoint_schema.md` when the plan needs structure.
3. During planning, ask the user which CP-FINAL quality gate to use. Prefer `AskUserQuestion` when the host provides it; otherwise ask a concise plain-text question with the same three choices:
   - `SubAgents Review`: use the host's parallel sub-agent review mechanism.
   - `Codex Review`: run a Codex-style structured review and the official Codex review entrypoint in parallel, then merge the results.
   - `Claude Review`: run the existing structured Claude review and Claude CLI's official `/review` command in parallel, then merge the results.
4. Build a goal objective that includes the source plan, checkpoint list, publication checkpoint, selected final quality gate, and completion rules. Use `references/goal_objective_template.md` when composing the objective.
5. Start or continue goal-mode work with that objective. Keep the objective as the source of truth after context reset; if the objective would be too large, write a task file first and reference it from the goal.
6. Work checkpoint by checkpoint. After each checkpoint, record evidence: changed files, tests, manual checks, known residual risk, and whether a review is now required.
7. Before CP-FINAL, publish the finished work: create debt-unit commits using Conventional Commit messages, push the branch, and create a PR. The PR title MUST also be in Conventional Commit format.
8. For commit message and PR title type/scope decisions, instruct the agent to use the separate `commit skills` skill when it is available. Do not duplicate the Conventional Commit rulebook here; this skill owns the requirement and evidence, while `commit skills` owns naming conventions.
9. At CP-FINAL, run the selected quality gate exactly as recorded in the objective. Parse or normalize the merged result into the shared `status` / `findings` contract.
10. Treat `CHANGES_REQUESTED` as new checkpoint work. Convert each actionable finding into a checkpoint, fix it, verify it, make any additional debt-unit Conventional Commit(s), update the PR, and re-run the selected gate.
11. Call `update_goal(status="complete")` only when all checkpoints are done, publication evidence exists, and the selected final quality gate is `ACCEPTED`.

## Publication Rules

- Add a publication checkpoint before CP-FINAL unless the user explicitly says not to commit or not to create a PR.
- Group commits by debt unit: each commit should correspond to one coherent implementation, test, documentation, or review-fix concern. A small task may have one commit if it is truly one debt unit.
- Use Conventional Commit format for every commit message and for the PR title.
- When composing commit messages or the PR title, reference `commit skills` as the source of truth for Conventional Commit type/scope selection and formatting.
- The PR body should state the goal, what changed, verification evidence, and residual risks or skipped checks.
- Record publication evidence: `git status`, `git log <base>..HEAD`, pushed branch, PR URL, PR title, and the PR body path or summary.

## CP-FINAL Execution Rule

CP-FINAL must execute the quality gate chosen during planning. Do not silently substitute another gate after implementation. If the chosen gate cannot run, mark the review result `UNKNOWN` and ask the user whether to switch gates; do not self-approve.

## Review Gate Rules

- Record the selected gate name and exact execution plan in CP-FINAL before implementation starts.
- Run multiple reviewers inside a selected gate in parallel whenever the host/runtime supports parallel execution. If parallel execution is unavailable, run both reviewers before merging and note that they were sequential.
- Require the merged review result to use `status: "ACCEPTED"`, `status: "CHANGES_REQUESTED"`, or `status: "UNKNOWN"` plus a `findings` array when findings exist.
- Use `scripts/validate_review_acceptance.py` when a deterministic local check is useful for review output from a file or stdin.
- If any reviewer returns actionable blocking findings, the merged status is `CHANGES_REQUESTED`.
- If any required reviewer is unavailable, times out, or returns ambiguous output, the merged status is `UNKNOWN` unless another selected reviewer clearly returns `CHANGES_REQUESTED`.
- If a reviewer gives prose without structured status, classify it as `UNKNOWN`; do not treat it as accepted or as actionable requested changes.
- Do not treat self-review by the implementing agent as CP-FINAL evidence unless the user explicitly selected a self-review fallback.
- Never mark the goal complete because token budget, time budget, or patience is exhausted.

## Quality Gate Shapes

### SubAgents Review

Use this gate only when the user selects it. Spawn or request three independent reviewers in parallel when the host supports sub-agents:

- Implementation reviewer: checks behavior against the checkpoint plan and inspects likely code paths.
- Verification reviewer: checks tests, commands, manual evidence, and missing coverage.
- Scope reviewer: checks unintended changes, user constraints, compatibility/fallback policy, and dirty worktree boundaries.

Each sub-agent must receive the checkpoint list, changed-file summary, verification evidence, publication evidence, user constraints, and the response contract from `references/review_gate.md`. Do not pass the implementer's conclusions as ground truth. Merge their results with the Review Gate Rules above.

### Codex Review

Use this gate only when the user selects it and a Codex runtime is available. Run both of these reviewer paths in parallel and merge them:

- Structured Codex review: invoke Codex non-interactively with the same review prompt shape used by `scripts/run_claude_review.py`, asking for the shared JSON contract.
- Official Codex review: invoke the official Codex review entrypoint provided by the runtime, such as a `/review` slash command or non-interactive `review` command.

The structured path provides the machine contract. The official path provides the runtime's native review behavior. If the official path returns prose, summarize concrete blocking findings into the shared contract before merging.

### Claude Review

Use this gate only when the user selects it and a Claude runtime is available. Run both of these reviewer paths in parallel and merge them:

- Structured Claude review: use `scripts/run_claude_review.py` or an equivalent `claude -p` invocation with the shared JSON contract.
- Official Claude review: invoke Claude CLI's official review command, normally `claude -p "/review pr#<number>"`.

Give the structured reviewer the checkpoint list, changed-file summary, verification evidence, publication evidence, user constraints, and the required response contract from `references/review_gate.md`. Give the official reviewer the PR target and any concise review instructions that fit the `/review` command. Do not ask either reviewer to redo implementation.

The helper keeps OAuth/subscription login compatible by default. It uses `--output-format json`, a JSON schema, model defaults, default permission mode, read-only review tools, strict MCP config, and a bounded budget. This mode is not fully hermetic: Claude may still read normal settings, hooks, and CLAUDE.md context that apply to the subprocess. Use `--hermetic` only when `ANTHROPIC_API_KEY` or `apiKeyHelper` is available and the user explicitly wants `claude --bare` isolation.

Keep review inputs compact for every gate. Summarize broad diffs into checkpoint evidence and changed-file lists before invoking reviewers; pass detailed files only when a finding depends on them. The Claude helper saves the exact prompt as `<review.out>.prompt.md` by default, so inspect that file when Claude times out or returns an ambiguous result.

## Resources

- `references/checkpoint_schema.md`: Checkpoint format and decomposition rules.
- `references/goal_objective_template.md`: Goal objective template for context-reset handoff.
- `references/review_gate.md`: Review status contract and reviewer prompt skeleton.
- `references/review_schema.json`: Shared structured review schema for runtimes that accept output schemas.
- `scripts/run_claude_review.py`: Build and run the default `claude -p` acceptance review.
- `scripts/validate_review_acceptance.py`: Deterministic `ACCEPTED`/`CHANGES_REQUESTED` classifier for review output.
