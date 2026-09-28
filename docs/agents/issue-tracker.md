# Issue tracker: local Markdown

Issues and PRDs live as markdown files under `.scratch/`. GitHub issues are the inbox for
user reports; accepted reports are mirrored into `.scratch/` and tracked there.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- Raw notes: `.scratch/<feature-slug>/idea.md`
- PRD (optional): `.scratch/<feature-slug>/PRD.md`
- Issues: `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- Triage state: a `Status:` line near the top of each issue (labels: `triage-labels.md`).
  Keep the label alone on the line; put reasoning in a `> **Status note.**` below it.
- Comments and conversation history append to the bottom under `## Comments`.
- An issue that mirrors a GitHub issue says so in a `GitHub:` line under `Status:`.

## Issue templates

- **Bug:** `issue-template-bug.md` — Symptom / Reproduction / Root cause / Fix / Verification / …
- **Feature / refactor:** `issue-template-feature.md` — What to build / Decisions / Acceptance criteria / …

Before writing an issue, read the most recent sibling issues and copy the structure they use.

## Branch isolation (per feature)

- **One branch `<slug>-rN` per feature**, cut from local `master`, shared by all of that
  feature's issues. Never one branch per issue, never code directly on `master`.
- **Clean tree before switching branches** — commit or stash first.
- **Docs escape hatch:** docs, `.scratch/`, markdown, and agent-workflow files go straight to
  `master`.
- **Merge is agent-executed, human-gated.** `/finish-feature` runs the tests, runs
  `/code-review`, asks *merge now?*, then squash-merges, re-runs tests, and flips the tracker.
  Agents never `git push` without approval.

### Status-flip timing

An issue flips to `completed` on the feature branch when its commit lands. On `master` it
reads `on-branch` until the feature squash-merges.

### The feature tracker (`.feature-status.md`)

Kept on `master` at the feature root (outside `issues/`):

```markdown
status: in-progress        # in-progress | awaiting-review | post-merge-test-failed | merged
branch: <slug>-rN
round: N
issues:
  - <NN>-<slug>
```

### Extending a shipped feature

Add new issue files to the existing `.scratch/<slug>/` folder and cut `<slug>-r(N+1)` from
current `master`. Never reopen a terminal issue (`completed` / `wontfix` / `superseded` /
`closed`) — file a new one.

## Decision records

When `/grill-me` or `/grill-with-docs` runs against an issue, append the resolved decisions
under a dated heading:

```markdown
## Decisions taken during /grill-me on <YYYY-MM-DD>

### D1. Short decision title

The choice, why, alternatives rejected, consequences.
```

Numbers are sequential per issue and never reused. A later session continues the numbering.
Locked decisions are not re-litigated without a new session. Decisions that outlive one
feature become an ADR in `docs/adr/`.

## Implementation Summary

At issue close, the same commit that contains the code must:

1. Flip `Status:` to `completed`.
2. Fill `## Implementation Summary`:

```markdown
## Implementation Summary

**Completed:** 2026-10-01, commit abc1234

- What was built (behaviour, not implementation detail)
- Tests added (number and type)
- Test results (e.g. "all 55 tests pass")
- Manual Fusion smoke: what was checked, by whom
```

Fusion-only behaviour can't be proven by pytest. If the manual smoke hasn't been done yet,
commit with `Status: ready-for-human` instead of `completed`; flip it to `completed` once the
user confirms the smoke test.

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/` (creating the folder if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path.
