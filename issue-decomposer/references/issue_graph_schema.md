# Issue Graph Schema

Use this reference when deciding the parent issue, Epic, and sub-issue structure.

## Epic Decision Rules

Decide whether to create an Epic automatically from the size and coordination cost of the source problem.

Create an Epic when most of these are true:

- The request spans three or more independently valuable outcomes, domains, workflows, teams, or release risks.
- The work needs a durable roll-up for status, sequencing, dependencies, or stakeholder acceptance.
- The source problem has a shared business goal, but the child work can be implemented and reviewed separately.
- Closing the parent itself would not prove implementation; completion is better represented by all required child issues being closed.

Do not create an Epic when most of these are true:

- One issue can state the outcome, scope, acceptance criteria, and verification path without becoming hard to review.
- The split would only mirror implementation layers such as frontend/backend/tests or produce commit-sized tasks.
- There are only one or two child issues and a checklist in the main issue is enough.
- The requested work is exploratory, vague, or not yet accepted as roadmap scope; draft a single discovery issue instead.

When creating an Epic:

- Title it as a roll-up outcome, usually `[Epic] <domain or release outcome>`, unless the repository already uses another convention.
- Treat it as a management parent only. Do not assign implementation tasks, code ownership, or detailed delivery checkpoints to the Epic itself.
- Put implementation work in Sub-Issues that each have their own acceptance criteria and verification hints.
- Keep the number of Sub-Issues small enough to reduce coordination cost. Prefer 3-7 child issues for most Epics; split beyond that only when the work has clearly separate owners, sequencing, or risk profiles.
- If a candidate child issue is not independently valuable or reviewable, keep it as a checklist item or handoff checkpoint instead of creating another issue.

## Decomposition Rules

- Split first by business domain, user workflow, data lifecycle, or operational boundary.
- Keep implementation checkpoints out of the issue graph unless they are independently valuable deliverables.
- Create a parent issue or Epic when several sub-issues share one release goal, acceptance boundary, or stakeholder narrative.
- Create a sub-issue when the work can be implemented, verified, and reviewed without completing every sibling.
- Create a cross-cutting issue only when the concern affects multiple domains and needs its own acceptance criteria, such as observability, migration, security, or CI.
- Do not create duplicate issues for frontend/backend halves unless the user outcome genuinely requires separate tracking.

## Parent Issue Record

```yaml
title: "Domain or outcome name"
purpose: "Why this issue group exists"
source_context:
  - "Inline facts from the user request or source note"
scope:
  in:
    - "Domain outcome included"
  out:
    - "Explicit non-goal"
sub_issues:
  - key: "short-stable-key"
    title: "Sub-issue title"
    outcome: "Independent business/user outcome"
    dependency: "none or another key"
acceptance:
  - "Release-level observable acceptance"
labels:
  - "existing repo label"
handoff_to_goal_checkpoint_runner:
  - "Implementation areas likely to become checkpoints later"
```

## Epic Record

Use the parent issue record for Epics, with these stricter semantics:

```yaml
title: "[Epic] Domain or release outcome"
purpose: "Management roll-up for child issues; not an implementation task"
source_context:
  - "Inline facts from the user request or source note"
scope:
  in:
    - "Shared outcome coordinated by the Epic"
  out:
    - "Implementation tasks owned by Sub-Issues"
sub_issues:
  - key: "short-stable-key"
    title: "Sub-issue title"
    outcome: "Independent business/user outcome"
    dependency: "none or another key"
acceptance:
  - "All required Sub-Issues are closed and release-level acceptance is satisfied"
labels:
  - "existing repo label"
assignment: "none"
handoff_to_goal_checkpoint_runner:
  - "Run goal-checkpoint-runner on the selected Sub-Issue, not on the Epic itself"
```

## Sub-Issue Record

```yaml
title: "Outcome-oriented title"
parent: "Parent issue or Epic title"
domain: "Bounded domain, workflow, or cross-cutting concern"
problem: "Concrete problem this issue resolves"
scope:
  in:
    - "Behavior, artifact, or constraint covered"
  out:
    - "Nearby concern intentionally excluded"
acceptance:
  - "Observable condition"
verification_hints:
  - "Likely tests, commands, screenshots, or manual checks"
dependencies:
  - "Issue key or none"
labels:
  - "existing repo label"
checkpoint_hints:
  - "Implementation checkpoint candidate for goal-checkpoint-runner"
```

## Split Smells

- Too broad: the issue has multiple unrelated actors, lifecycle stages, or release risks.
- Too narrow: the issue title is a code edit, test command, refactor step, or commit-sized action.
- Noisy graph: the Epic has many children that are really checklist items, checkpoint hints, or layer splits with the same acceptance path.
- Poor parent: the parent only restates a folder name and does not define a product/domain outcome.
- Poor sub-issue: the sub-issue cannot be accepted without reading sibling issue bodies.
- Missing domain: the issue is organized around implementation layers only, with no user or business boundary.

## GitHub Publication Notes

`gh issue create` can create normal issues, but it cannot create first-class GitHub Sub-Issue relationships. When Sub-Issues are required, use `gh api` so the issue node IDs are available and the relationship can be linked through GraphQL.

Recommended flow:

1. Resolve the repository ID if creating issues through GraphQL, or create each issue through REST and keep the returned `node_id`.
2. Create the Epic or parent issue first with `gh api repos/:owner/:repo/issues`.
3. Create each Sub-Issue with `gh api repos/:owner/:repo/issues`.
4. Link each child with the GraphQL `addSubIssue` mutation using the parent `node_id` and child `node_id`.
5. Update the Epic or parent body with a readable checklist of child issue numbers or URLs after linkage.

Example linkage command:

```sh
gh api graphql \
  -f parentId="PARENT_NODE_ID" \
  -f childId="CHILD_NODE_ID" \
  -f query='
mutation($parentId: ID!, $childId: ID!) {
  addSubIssue(input: {issueId: $parentId, subIssueId: $childId}) {
    issue { number url }
    subIssue { number url }
  }
}'
```

If the repository or account does not support first-class Sub-Issues, fall back to normal issues plus a parent-body checklist, and report that limitation clearly.
