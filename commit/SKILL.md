---
name: commit
description: Enforce Conventional Commits for commit messages and pull request titles. Use when Codex needs to write, review, validate, or choose a git commit message, PR title, squash-merge title, or release-relevant change summary, especially before running git commit or opening/updating a PR.
---

# Commit

## Overview

Use this skill to produce and validate commit messages and PR titles that follow the allowed Conventional Commits subset and the repository's commit-content policy. PR titles follow the same header rules because squash merges use the PR title as the final commit message.

Individual commits are accountable units owned by the human author who uses the tool. Do not add AI co-author trailers to individual commits. If a change needs enough explanation to require a body, split the change into smaller commits or put the explanation in the PR or squash-commit body instead.

## Required Form

Use this header form:

```text
<type>(<scope>)!: <title>
```

The scope and `!` are optional. The colon and following space are required.

Allowed types:

```text
chore, ci, docs, feat, fix, perf, refactor, revert, style, test
```

Use `feat` when the change adds application or library functionality. Use `fix` when the change fixes an application bug. Use another allowed type only when the change is not a feature or bug fix.

Write generated headers in lowercase for type and scope even though parsing is case-insensitive except for `BREAKING CHANGE`.

Keep the title to one debt-unit change. Do not join separate changes with `and`.

Bad:

```text
fix(api): validate tokens and refresh session state
```

Good split:

```text
fix(api): validate tokens
fix(session): refresh session state
```

## Scope

Add a scope only when it clarifies the affected codebase section. Make it a short noun in parentheses.

Examples:

```text
fix(parser): handle arrays with repeated spaces
docs(api): update authentication examples
```

## Body And Footers

For individual commits, do not add a body or footers. Use a title-only commit message.

Use a body only for PR descriptions or squash-commit messages where the final merge commit needs release-level context. Start the body after one blank line below the title.

Add footers after one blank line below the body. Each footer uses a token, then `: ` or ` #`, then a value. Footer tokens use `-` instead of spaces, except `BREAKING CHANGE`, which is allowed. Treat `BREAKING-CHANGE` as the same token as `BREAKING CHANGE`.

Examples:

```text
Refs: #123
Acked-by: Jane Doe
BREAKING CHANGE: environment variables now take precedence over config files
```

Do not add `Co-authored-by` trailers to individual commits. The human operating the AI tool owns the commit. If a squash commit needs human co-author attribution, keep that attribution at the squash-merge layer rather than on each debt-unit commit.

## Breaking Changes

Mark every breaking change with either `!` in the header or a `BREAKING CHANGE:` footer.

For individual commits, prefer `!` because individual commit messages are title-only:

```text
feat(api)!: require signed webhook payloads
```

For PR titles, prefer `!` because titles cannot carry footers:

```text
feat(api)!: require signed webhook payloads
```

If `!` is used, the title must describe the breaking change clearly enough without relying on a footer.

## Validation

Before committing or publishing a PR title, validate the candidate with `scripts/validate_conventional_commit.py`.

Validate a PR title:

```bash
python3 /Users/cat/repos/skills/commit/scripts/validate_conventional_commit.py --title-only "fix(parser): handle arrays with repeated spaces"
```

Validate an individual commit message file:

```bash
python3 /Users/cat/repos/skills/commit/scripts/validate_conventional_commit.py --file /path/to/commit-message.txt
```

This rejects individual commit bodies, `Co-authored-by` trailers, and titles that combine separate debt units with `and`.

Validate a squash-commit message file when a body or footers are intentionally part of the final merge commit:

```bash
python3 /Users/cat/repos/skills/commit/scripts/validate_conventional_commit.py --squash --file /path/to/squash-message.txt
```
