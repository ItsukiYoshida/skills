---
name: issue-decomposer
description: Use when turning a rough product request, business domain, PR debt, roadmap item, or design note into GitHub-ready issues. This skill decomposes work by domain and user/business outcome, drafts parent issues and sub-issues, chooses repository-appropriate existing labels, checks for duplicate tracking, and prepares issue bodies that hand off cleanly to goal-checkpoint-runner for later implementation checkpointing.
---

# Issue Decomposer

## Purpose

Use this skill before implementation planning. Its job is to produce a high-quality issue graph: parent issues, sub-issues, labels, dependencies, and self-contained bodies that preserve the domain reasoning. Leave fine-grained implementation checkpoints to `goal-checkpoint-runner`.

## Workflow

1. Establish the source of truth. Read the user's source note, PR diff, issue thread, product request, or repository document explicitly named by the user. Preserve exact names, identifiers, repo names, branch names, and quoted wording.
2. Inspect the target repository before drafting:
   - Existing issue templates: `.github/ISSUE_TEMPLATE/**`, `ISSUE_TEMPLATE.md`.
   - Existing labels: prefer `gh label list --json name,description,color` when GitHub is available.
   - Existing tracking: use `gh issue list --state open --json number,title,body,labels` and targeted `gh issue search` queries when publication may create duplicates.
   - Existing docs or architecture notes only when they are directly relevant to the source request.
3. Decompose by domain outcome, not by implementation step. Use `references/issue_graph_schema.md` for the issue graph format, Epic decision rules, and splitting rules.
4. Choose labels from the repository's existing label vocabulary. Use `references/label_strategy.md` for mapping priorities, issue types, domains, and status labels. Do not invent or create labels unless the user asks for label creation or the repo clearly has an established missing-label convention.
5. Draft issue bodies with enough inline context that the issue can be implemented without opening the original planning note. Use `references/issue_body_templates.md` for parent and sub-issue bodies.
6. Connect to `goal-checkpoint-runner` explicitly:
   - Parent issues define the business/domain boundary and release-level acceptance.
   - Sub-issues define independently valuable outcomes and constraints.
   - Add a short handoff section that says what should become checkpoints during implementation, but do not pre-expand every checkpoint unless the user asks.
7. If publishing, create or update issues only after duplicate checks:
   - Use `gh issue create --title ... --body-file ... --label ...` only for standalone issues or parent issues that will not need first-class Sub-Issue linkage.
   - When first-class Sub-Issues are needed, use `gh api` for issue creation/linkage because `gh issue create` cannot create GitHub Sub-Issue relationships. Follow the publication notes in `references/issue_graph_schema.md`.
   - Use `gh issue edit --body-file ...` for body updates after publication.
8. After publishing, update the parent or Epic body with child issue numbers or URLs as a human-readable index even when first-class Sub-Issue linkage succeeds. Report created issue numbers, labels, linkage method, and any skipped duplicates.

## Issue Quality Bar

- One issue should own one domain outcome or one cross-cutting concern with a clear acceptance boundary.
- Sub-issues should be independently schedulable and reviewable; avoid splitting into purely mechanical commits or internal checkpoint steps.
- Create an Epic automatically only when the requested problem is large enough to need a management parent across several independently valuable issues. The Epic is a tracking parent only: do not assign implementation tasks to the Epic itself.
- Bodies must be self-contained. Links are allowed as supporting references, but not as the only source of requirements.
- Acceptance criteria must be observable from code, UI behavior, tests, documentation, deployment state, or a manual verification path.
- Dependencies must be explicit when order matters. If order does not matter, say so through the parent issue checklist rather than inventing dependencies.
- Labels must match the target repo's vocabulary. If no useful label exists, omit it and mention the gap instead of adding noisy labels.

## Resources

- `references/issue_graph_schema.md`: Domain decomposition rules, Epic decision rules, issue graph format, and Sub-Issue publication notes.
- `references/issue_body_templates.md`: Parent issue and sub-issue body templates.
- `references/label_strategy.md`: Repository label inspection and selection rules.
