# Review Gate Contract

The review gate decides whether the goal can be completed. It is not a generic style review; it checks the completed checkpoints against the user's plan and the collected evidence.

During planning, choose exactly one gate with `AskUserQuestion` when available:

- `SubAgents Review`: three host-provided sub-agent reviewers run in parallel.
- `Codex Review`: structured Codex review plus the official Codex `/review` or review command run in parallel.
- `Claude Review`: structured Claude review plus Claude CLI's official `/review` command run in parallel.

The selected gate must be recorded in the goal objective before implementation starts. Review gates never authorize PR merging: do not merge a PR, enable auto-merge, approve a merge queue entry, or perform an equivalent repository-host merge action, even if the user explicitly asks or grants permission.

## Machine Contract

Review output must be a JSON object matching this shape:

```json
{
  "status": "ACCEPTED",
  "summary": "All checkpoints are satisfied.",
  "findings": []
}
```

or:

```json
{
  "status": "CHANGES_REQUESTED",
  "summary": "Required fixes remain.",
  "findings": [
    {
      "checkpoint": "CP-002",
      "severity": "high",
      "file": "path/to/file.ts",
      "line": 42,
      "problem": "Missing test for failed API response.",
      "required_fix": "Add a regression test covering the error branch."
    }
  ]
}
```

`ACCEPTED` with non-empty findings is treated as `CHANGES_REQUESTED`.

## Reviewer Prompt Skeleton

```text
You are reviewing a checkpointed goal implementation.

Selected quality gate:

Reviewer role for this invocation:
- Implementation reviewer
- Verification reviewer
- Scope reviewer

Inputs:
- Goal objective:
- Checkpoints and statuses:
- Changed files:
- Verification evidence:
- Publication evidence:
  - Debt-unit commit list:
  - Pushed branch:
  - PR URL:
  - PR title:
  - PR body path or summary:
- User constraints:

Hard prohibition:
- Do not implement changes.
- Do not edit files, push commits, approve the PR, merge the PR, enable auto-merge, close the PR, or mutate the PR in any way.

Review focus:
- Does the implementation satisfy every checkpoint acceptance criterion?
- Is the verification evidence sufficient for the risk and blast radius?
- Are the commits split by debt unit, and are commit messages plus the PR title in Conventional Commit format?
- Was `commit skills` used or referenced for Conventional Commit type/scope decisions when available?
- Are there unintended scope changes, fallback behavior, or contract drift?

Return only the required JSON object.
```

## Gate Execution

### Claude Review

Run the structured Claude review and Claude CLI's official `/review` command in parallel. Both paths are review-only and must not mutate files or PR state.

Use the bundled helper for the structured Claude path when possible:

```bash
python3 /path/to/goal-checkpoint-runner/scripts/run_claude_review.py \
  --goal-objective goal.md \
  --evidence evidence.md \
  --output review.structured.out \
  --timeout-sec 300
```

The official path should invoke Claude CLI's `/review` command against the published PR and save that output separately:

```bash
claude -p "/review pr#<number>

Review only. Do not edit files, push commits, approve the PR, merge the PR, enable auto-merge, close the PR, or mutate the PR in any way." > review.official.out
```

Use the PR number or PR URL from CP-PUBLISH evidence. Add concise extra review instructions to the prompt only when needed.

The helper runs `claude -p` with structured JSON output, writes Claude's raw output, classifies it with `validate_review_acceptance.py`, and exits:

- `0`: review is clearly `ACCEPTED`
- `1`: review is `CHANGES_REQUESTED`
- `2`: reviewer is unavailable, timed out, failed, or returned ambiguous output

The helper writes the generated prompt to `<review.out>.prompt.md` by default, then passes that file to `claude -p` over stdin. This keeps large review context out of `ps` output, leaves an inspectable prompt artifact, and makes timeout handling reliable.

To reuse a prebuilt prompt:

```bash
python3 /path/to/goal-checkpoint-runner/scripts/run_claude_review.py \
  --prompt-file /tmp/review-prompt.md \
  --output review.structured.out
```

The helper defaults are intentionally review-scoped and OAuth compatible:

- No `--bare` by default, so Claude subscription/OAuth/keychain auth continues to work.
- `--strict-mcp-config` without MCP config to avoid ambient MCP startup.
- `--model opus --fallback-model sonnet` for consistent review quality.
- `--permission-mode default` with read-only review tools and write tools denied.
- `--max-budget-usd 2` and `--timeout-sec 300` to bound runaway reviews while leaving enough time for real file inspection.
- `--hermetic` is opt-in and maps to `claude --bare`; it requires `ANTHROPIC_API_KEY` or an `apiKeyHelper` setting because OAuth/keychain auth is disabled by Claude in bare mode. The helper checks this before invoking Claude and returns `UNKNOWN` with `claude_auth_missing_for_hermetic` when auth is unavailable.

OAuth-compatible mode is intentionally less isolated than `--bare`. It avoids ambient MCP startup with `--strict-mcp-config`, but normal Claude settings, hooks, and CLAUDE.md context can still affect the subprocess. Use `--hermetic --settings '{"apiKeyHelper":"..."}'` or `ANTHROPIC_API_KEY` when full bare-mode isolation matters more than subscription/OAuth compatibility.

Manual invocation should preserve the same shape. The example below is abbreviated; prefer the helper for the full `--add-dir`, dynamic-system-prompt exclusion, budget, fallback model, allowed-tool, and disallowed-tool defaults.

```bash
claude -p \
  --model opus \
  --fallback-model sonnet \
  --output-format json \
  --json-schema '<status/findings schema>' \
  --permission-mode default \
  --strict-mcp-config \
  --no-session-persistence \
  --exclude-dynamic-system-prompt-sections \
  --max-budget-usd 2 \
  --add-dir "$(pwd)" \
  --allowedTools Read Grep Glob 'Bash(git diff:*)' 'Bash(git log:*)' 'Bash(git status:*)' \
  --disallowedTools Edit Write MultiEdit NotebookEdit \
  < review-prompt.md
```

### Codex Review

Run the structured Codex review and the official Codex `/review` or review command in parallel. Both paths are review-only and must not mutate files or PR state.

For the structured path, use the same prompt skeleton and JSON schema as the Claude structured path. A non-interactive runtime may look like:

```bash
codex exec \
  --output-schema /path/to/goal-checkpoint-runner/references/review_schema.json \
  -o review.structured.out \
  - < review-prompt.md
```

For the official path, invoke the active Codex runtime's official review entrypoint with the same context and save it separately, for example `review.official.out`. Include review-only instructions that forbid file edits, pushes, PR approval, PR merge, auto-merge, closing, or other PR mutation.

### SubAgents Review

Run three independent host-provided reviewers in parallel:

- Implementation reviewer
- Verification reviewer
- Scope reviewer

Each reviewer receives only the goal, checkpoint statuses, changed files, publication evidence, verification evidence, user constraints, and this review contract. Do not pass the implementer's conclusion as ground truth. Save each raw output separately and normalize each result before aggregation.

### Review Aggregation Rule

- If any required reviewer reports concrete blocking findings, aggregated status is `CHANGES_REQUESTED`.
- If a required reviewer is unavailable, times out, or returns ambiguous prose, aggregated status is `UNKNOWN` unless another required reviewer clearly returns `CHANGES_REQUESTED`.
- Aggregated status is `ACCEPTED` only when all required reviewers for the selected gate are available and have no blocking findings.
- Preserve raw reviewer outputs and the normalized aggregated JSON as CP-FINAL evidence.

## Classification Guidance

- Advisory improvements do not block acceptance unless they contradict the user's constraints or acceptance criteria.
- Missing verification blocks acceptance when the checkpoint touches shared contracts, user-visible behavior, persistence, security, deployment, or long-lived automation.
- Ambiguous review output is `UNKNOWN`, not `ACCEPTED` and not `CHANGES_REQUESTED`.
