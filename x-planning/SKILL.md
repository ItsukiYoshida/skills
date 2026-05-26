---
name: x-planning
description: Use only in Codex Plan mode to turn vague implementation wishes, GitHub issues, or user-described tasks into a strict implementation plan that starts with $goal-checkpoint-runner. Trigger when the user wants to decide what to build, refine loose requirements through questions, choose from repository issues, or prepare a goal-checkpoint-runner-ready plan before implementation. Reject use outside Plan mode.
---

# X Planning

## Mode Gate

Use this skill only in Plan mode.

If the current turn is not running in Plan mode, reject the request immediately:

```text
This skill must be used in Plan mode because it relies on Plan-mode requirement gathering and ask flow. Switch to Plan mode and invoke $x-planning again.
```

Do not inspect issues, draft a plan, spawn agents, or call `$goal-checkpoint-runner` outside Plan mode.

## Purpose

Use this skill before `$goal-checkpoint-runner`. Its job is to make ambiguous work precise enough for implementation. It does not decompose finished requirements into checkpoint execution details; leave CP splitting, goal-mode operation, and the final review gate to `$goal-checkpoint-runner`.

The final output is a user-approved implementation plan whose first line is:

```text
$goal-checkpoint-runner
```

## Workflow

### 1. Establish the Task Candidate

Start by asking the user what they want to do.

Before asking, inspect nearby GitHub issues through `gh` and include a few relevant candidates in the question:

```bash
gh issue list --limit 20 --state open
```

If the user has already named an issue number, issue URL, branch, file path, or concrete task, fetch that context first and focus the question on confirming scope:

```bash
gh issue view <number>
```

If `gh` is unavailable, unauthenticated, or the directory is not a GitHub repo, say that issue lookup was unavailable and ask for the task directly. Do not block the planning flow solely on issue lookup.

Ask in Plan mode using the available ask mechanism. Offer issue-number selection and a free-form task path, because the desired work may not be in GitHub issues.

### 2. Gather Context Conservatively

Read the exact artifacts that define the work:

- GitHub issue body, comments, labels, and linked PRs when the task came from an issue.
- Existing docs, tests, route definitions, UI surfaces, configs, or commands named by the user.
- Repo-native templates such as issue templates, PR templates, Justfiles, Makefiles, and contributor docs when they affect expected workflow.
- Current branch and dirty worktree status before recommending implementation steps.

Prefer facts from the repository and live tool output over assumptions. If the task depends on an external service or live environment, identify what must be verified later instead of inventing certainty.

### 3. Tighten Requirements Through Plan-Mode Ask

Use short, focused asks to resolve only decisions that materially change implementation:

- User-visible behavior and success criteria.
- Inputs, outputs, API contracts, data formats, or UI states.
- Compatibility and fallback policy.
- Scope boundaries and explicit non-goals.
- Migration, rollout, or operational constraints.
- Verification expectations and acceptable manual checks.

Avoid asking for implementation decomposition too early. The planning skill should turn fuzzy intent into a strict target; `$goal-checkpoint-runner` will split that target into checkpoints.

When the user answers with an issue number, inspect that issue and ask only the missing contract questions. When the user answers with free-form requirements, map them to existing repo flows before proposing new surfaces.

### 4. Use Subagents for Context, Not Implementation

Use subagents when independent context gathering will reduce uncertainty:

- Use explorer agents for well-scoped repo questions such as "which route owns this behavior?", "what tests cover this flow?", or "where is this admin default consumed?"
- Run multiple explorers in parallel when the questions are independent.
- Reuse an explorer for follow-up questions on the same area.

Tell every subagent that they are not alone in the codebase and must not edit files. Planning subagents should return evidence, file references, risks, and open questions only.

Do not spawn worker agents for implementation from this skill. Implementation belongs to the later `$goal-checkpoint-runner` phase after the plan is accepted.

### 5. Produce the Implementation Plan

After requirements are clear enough, produce a concise plan for user confirmation. The plan must be actionable by `$goal-checkpoint-runner` and should contain:

- Source task: issue number/URL or user-provided task statement.
- Objective: one paragraph describing the exact desired outcome.
- Confirmed requirements: behavior, contracts, data, UI, docs, and operational constraints.
- Explicit non-goals and rejected fallback/backcompat paths.
- Relevant repo context: files, modules, commands, and existing flows to preserve.
- Verification expectations: tests, commands, manual checks, screenshots, live checks, or review evidence expected after implementation.
- Risks and questions: only unresolved items that must be settled before or during implementation.
- Suggested checkpoint boundaries: coarse responsibility boundaries only, not detailed CP records.

Start the plan with the exact invocation line:

```text
$goal-checkpoint-runner
```

Do not write the final plan as `$goal-checkout-runner`; the implementation skill name is `$goal-checkpoint-runner`.

### 6. Handoff Rules

Make the handoff explicit:

- State that `$goal-checkpoint-runner` should convert the accepted plan into CP records, create or continue the goal, execute checkpoints, collect evidence, and run its CP-FINAL review gate.
- Include any user constraints that affect checkpointing, such as commit boundaries, no-fallback policy, live-environment verification, or required docs/tests.
- Do not preemptively create a goal from this skill unless the user has accepted the plan and explicitly wants to begin implementation.

## Output Shape

Use this shape for the final plan:

```markdown
$goal-checkpoint-runner

## Source Task
...

## Objective
...

## Confirmed Requirements
...

## Non-Goals
...

## Repo Context
...

## Verification Expectations
...

## Risks And Open Questions
...

## Suggested Checkpoint Boundaries
...

## Handoff Notes
...
```

Keep the plan strict enough that a fresh implementation agent can run with it, but avoid duplicating `goal-checkpoint-runner`'s detailed checkpoint schema.
