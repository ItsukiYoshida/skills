# Review Gate Contract

The review gate decides whether the goal can be completed. It is not a generic style review; it checks the completed checkpoints against the user's plan and the collected evidence.

## Accepted Forms

Plain text:

```text
ACCEPTED
```

JSON:

```json
{
  "status": "ACCEPTED",
  "findings": []
}
```

## Changes Requested Forms

Plain text:

```text
CHANGES_REQUESTED
- CP-002: Missing test for failed API response.
- CP-004: Docs still mention removed fallback behavior.
```

JSON:

```json
{
  "status": "CHANGES_REQUESTED",
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

Return exactly one terminal status:
- ACCEPTED if no required fixes remain.
- CHANGES_REQUESTED if required fixes remain, followed by actionable findings.
```

## Default Claude Command

Use the bundled helper when possible:

```bash
python3 /path/to/goal-checkpoint-runner/scripts/run_claude_review.py \
  --goal-objective goal.md \
  --evidence evidence.md \
  --output review.out \
  --timeout-sec 180
```

The helper runs `claude -p`, writes Claude's review output, classifies it with `validate_review_acceptance.py`, and exits:

- `0`: review is clearly `ACCEPTED`
- `1`: review is `CHANGES_REQUESTED`
- `2`: review status is ambiguous or invalid

The helper writes the generated prompt to `<review.out>.prompt.md` by default, then passes that file to `claude -p` over stdin. This keeps large review context out of `ps` output, leaves an inspectable prompt artifact, and makes timeout handling reliable.

To reuse a prebuilt prompt:

```bash
python3 /path/to/goal-checkpoint-runner/scripts/run_claude_review.py \
  --prompt-file /tmp/review-prompt.md \
  --output review.out
```

If running manually, keep the same contract:

```bash
claude -p --output-format text --no-session-persistence < review-prompt.md
```

## Classification Guidance

- Advisory improvements do not block acceptance unless they contradict the user's constraints or acceptance criteria.
- Missing verification blocks acceptance when the checkpoint touches shared contracts, user-visible behavior, persistence, security, deployment, or long-lived automation.
- Ambiguous review output should be treated as `CHANGES_REQUESTED` until clarified.
