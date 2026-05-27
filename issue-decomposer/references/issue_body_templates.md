# Issue Body Templates

Use these templates as starting points. Keep the final body aligned with the target repository's issue templates when they exist.

## Parent Issue Template

```markdown
## 背景

<Source facts and domain context. Inline the important information; do not rely on a link as the only source of requirements.>

## 目的

<The business, product, or operational outcome this issue group should achieve.>

## スコープ

### 含む

- <Domain outcome included>

### 含まない

- <Explicit non-goal>

## Sub-Issues

- [ ] <Sub-issue title or URL after creation> - <one-line outcome>

## 受け入れ条件

- <Release-level observable acceptance criterion>

## ラベル方針

- <Existing labels that should apply to this parent>

## goal-checkpoint-runner への引き継ぎ

- <Which sub-issues or implementation areas should become checkpoints later>
- <Verification evidence expected at implementation time>
```

## Epic Issue Template

Use this when the decomposition rules call for an Epic. The Epic is a management parent only; do not include implementation tasks as Epic work.

```markdown
## 背景

<Source facts and domain context. Inline the important information; do not rely on a link as the only source of requirements.>

## 目的

<The business, product, or operational outcome this Epic coordinates.>

## 管理方針

- このEpicはSub-Issueの管理用であり、Epic自体には実装タスクを割り当てない。
- 実装、検証、レビュー可能な作業はSub-Issueで管理する。

## スコープ

### 含む

- <Shared outcome coordinated by this Epic>

### 含まない

- <Implementation task or nearby concern intentionally excluded>

## Sub-Issues

- [ ] <Sub-issue title or URL after creation> - <one-line outcome>

## 受け入れ条件

- <All required Sub-Issues are closed and release-level observable acceptance is satisfied>

## ラベル方針

- <Existing labels that should apply to this Epic>

## goal-checkpoint-runner への引き継ぎ

- <Run goal-checkpoint-runner on implementation Sub-Issues, not on this Epic>
```

## Sub-Issue Template

```markdown
## 背景

<Self-contained context for this sub-issue. Repeat the necessary parent context instead of requiring the reader to open the parent.>

## 解決したい問題

<One concrete problem or opportunity.>

## スコープ

### 含む

- <Behavior, artifact, or constraint covered by this issue>

### 含まない

- <Nearby concern intentionally left to another issue>

## 要件

- <Functional, domain, documentation, migration, or operational requirement>

## 受け入れ条件

- <Observable condition that proves this issue is complete>

## 検証観点

- <Likely command, test, manual check, screenshot, or review target>

## 依存関係

- <Parent issue, prerequisite issue, or "なし">

## goal-checkpoint-runner への引き継ぎ

- <Likely implementation checkpoint candidate>
- <Risk or compatibility point the final review should inspect>
```

## Body Rules

- Use the repository's language convention. If the repo commonly uses Japanese issues, write Japanese bodies unless the user asks otherwise.
- Expand important source-note content inline. A link can support the issue, but the body must still contain enough context to implement.
- Keep issue bodies about the desired outcome and constraints. Do not paste an implementation plan so detailed that it becomes stale before work starts.
- For Epics, keep the body focused on roll-up scope, child issue index, and release-level acceptance. Do not put assignable implementation work in the Epic body.
- Put metadata such as priority, type, and domain into labels when the repository has labels for them.
- Preserve exact identifiers from the source request: issue numbers, PR numbers, stack names, branch names, environment names, route names, API names, and quoted UI text.
