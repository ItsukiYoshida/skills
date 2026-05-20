# Review Gate Contract

The review gate decides whether the goal can be completed. It is not a generic style review; it checks the completed checkpoints against the user's plan and the collected evidence.

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
You are reviewing a checkpointed goal implementation through three roles:
- Implementation reviewer
- Verification reviewer
- Scope reviewer

Do not implement changes.

Inputs:
- Goal objective:
- Checkpoints and statuses:
- Changed files:
- Verification evidence:
- User constraints:

Review focus:
- Does the implementation satisfy every checkpoint acceptance criterion?
- Is the verification evidence sufficient for the risk and blast radius?
- Are there unintended scope changes, fallback behavior, or contract drift?

Return only the required JSON object.
```

## Default Claude Command

Use the bundled helper when possible:

```bash
python3 /path/to/goal-checkpoint-runner/scripts/run_claude_review.py \
  --goal-objective goal.md \
  --evidence evidence.md \
  --output review.out \
  --timeout-sec 300
```

The helper runs `claude -p` with structured JSON output, writes Claude's raw output, classifies it with `validate_review_acceptance.py`, and exits:

- `0`: review is clearly `ACCEPTED`
- `1`: review is `CHANGES_REQUESTED`
- `2`: reviewer is unavailable, timed out, failed, or returned ambiguous output

The helper writes the generated prompt to `<review.out>.prompt.md` by default, then passes that file to `claude -p` over stdin. This keeps large review context out of `ps` output, leaves an inspectable prompt artifact, and makes timeout handling reliable.

To reuse a prebuilt prompt:

```bash
python3 /path/to/goal-checkpoint-runner/scripts/run_claude_review.py \
  --prompt-file /tmp/review-prompt.md \
  --output review.out
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

## Classification Guidance

- Advisory improvements do not block acceptance unless they contradict the user's constraints or acceptance criteria.
- Missing verification blocks acceptance when the checkpoint touches shared contracts, user-visible behavior, persistence, security, deployment, or long-lived automation.
- Ambiguous review output is `UNKNOWN`, not `ACCEPTED` and not `CHANGES_REQUESTED`.
