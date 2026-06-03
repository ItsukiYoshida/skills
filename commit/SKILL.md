---
name: commit
description: Enforce Conventional Commits for commit messages and pull request titles. Use when Codex needs to write, review, validate, or choose a git commit message, PR title, squash-merge title, or release-relevant change summary, especially before running git commit or opening/updating a PR.
---

# Commit

## Overview

Use this skill to produce and validate commit messages and PR titles that follow the allowed Conventional Commits subset. PR titles follow the same rules because squash merges use the PR title as the final commit message.

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

## Scope

Add a scope only when it clarifies the affected codebase section. Make it a short noun in parentheses.

Examples:

```text
fix(parser): handle arrays with repeated spaces
docs(api): update authentication examples
```

## Body And Footers

Add a body only when the title is not enough. Start the body after one blank line below the title.

Add footers after one blank line below the body. Each footer uses a token, then `: ` or ` #`, then a value. Footer tokens use `-` instead of spaces, except `BREAKING CHANGE`, which is allowed. Treat `BREAKING-CHANGE` as the same token as `BREAKING CHANGE`.

Examples:

```text
Refs: #123
Acked-by: Jane Doe
BREAKING CHANGE: environment variables now take precedence over config files
```

## Breaking Changes

Mark every breaking change with either `!` in the header or a `BREAKING CHANGE:` footer.

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

Validate a commit message file:

```bash
python3 /Users/cat/repos/skills/commit/scripts/validate_conventional_commit.py --file /path/to/commit-message.txt
```
