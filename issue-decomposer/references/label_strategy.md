# Label Strategy

Use existing repository labels by default. Labels are metadata, not requirements; keep requirements in the issue body.

## Inspection Order

1. Check repository labels with `gh label list --json name,description,color` when GitHub access is available.
2. Check existing issue examples with `gh issue list --state all --limit 50 --json title,labels` when label meaning is unclear.
3. Check the repository's issue templates and contribution docs when label meaning is unclear from GitHub metadata.
4. If GitHub access is unavailable, use only repository templates/docs that are part of the source tree, then state that label selection is best-effort and should be verified before publication.

## Selection Rules

- Prefer repo-specific labels over generic guesses.
- Use at most one priority label unless the repo convention says otherwise.
- Use at most one primary type label, such as `bug`, `feature`, `enhancement`, `documentation`, `tech-debt`, or the repo's equivalent.
- Add domain labels only when the repo already uses them, such as `frontend`, `backend`, `infra`, `auth`, `billing`, or product-area labels.
- Add status labels only when creating a tracking issue in a workflow that already uses them, such as `blocked`, `needs-design`, or `ready`.
- Do not create labels during issue publication unless the user explicitly asked for label creation or approved a repo label taxonomy change.

## Mapping Heuristics

| Signal | Label category |
| --- | --- |
| User says urgent, release-blocking, production outage | highest existing priority label |
| Broken existing behavior | bug or defect label |
| New user/business capability | feature or enhancement label |
| Cleanup, migration, flaky workflow, maintainability | tech-debt or maintenance label |
| Docs-only output or source-of-truth correction | documentation label |
| CI, deployment, runtime config, observability | infra, ops, ci, or platform label |
| Domain-specific product area | existing domain/product label |

## Output Format

For each drafted issue, record:

```yaml
labels:
  selected:
    - "existing-label"
  omitted:
    - label: "candidate-label"
      reason: "not present in repository"
  confidence: "high | medium | low"
```
