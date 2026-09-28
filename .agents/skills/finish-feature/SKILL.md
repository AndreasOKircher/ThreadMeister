---
name: finish-feature
description: Close out a feature round opened by /start-feature. Runs the full test suite, auto-runs /code-review and triages its findings, then on a SINGLE human merge-approval squash-merges into master, re-runs the tests, flips the tracker, and deletes the branch. Asks before pushing. Use when all of a feature's issues are implemented on its branch.
---

# Finish Feature

Take a feature branch from "all issues implemented" to "merged on `master`" with **one**
human checkpoint: the merge decision, made after code review.

## When to use

- Every in-round issue is `completed` (or `ready-for-human` with its smoke test now done)
  on branch `<slug>-rN`.

## Process

### 1. Gate

- Each in-round issue reads `Status: completed` with an `## Implementation Summary`.
- Any issue at `ready-for-human` → ask the user to run its Fusion smoke test. Confirmed →
  flip it to `completed` and commit. Not confirmed → **stop**.
- `python -m pytest -q` — any failure → **stop**, report.
- User-visible change → `docs/changelog.md` updated; version bumped in
  `ThreadMeister.manifest` and `manifest.json` if this round ships a release.

### 2. Code review

Run `/code-review master...HEAD`.

### 3. Triage findings

- Apply the safe, high-confidence fixes on the branch; re-run pytest.
- File larger or uncertain findings as new issues in `.scratch/<slug>/issues/`.
- Report what was fixed vs filed.

### 4. One checkpoint

Ask: *"Tests green, review done (fixed X, filed Y). Squash-merge `<slug>-rN` into master now?"*
A "no" sets the tracker to `awaiting-review` and stops.

### 5. On approval

```
git checkout master
git merge --squash <slug>-rN
git commit -m "<slug> rN: <summary> (issues …)"
python -m pytest -q
```

- **Green** → set `.scratch/<slug>/.feature-status.md` to `status: merged`, flip the issues
  to `completed` on `master`, commit, then `git branch -D <slug>-rN`.
- **Red** → `git revert` the merge commit, set `status: post-merge-test-failed`, keep the
  branch, report.

### 6. Push

Never `git push` without explicit approval.

## Report

Test results, review outcome (fixed vs filed), merge SHA, tracker status, branch deleted,
next-round backlog.
