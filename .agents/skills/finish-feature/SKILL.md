---
name: finish-feature
description: Close out a feature round opened by /start-feature. Uses scripts/feature_flow.py for the mechanical steps (issue gate, full test run, push, PR, after-merge cleanup) and the model only for /code-review, triage and the PR text. The human squash-merges on GitHub (the single checkpoint). Use when all of a feature's issues are implemented on its branch.
---

# Finish Feature

Take a feature branch from "all issues implemented" to "open PR, ready to merge" with
**one** human checkpoint: clicking **Squash and merge** on GitHub, after code review.

**Mechanical steps are in `scripts/feature_flow.py`. Do not repeat them by hand.** The model
does only what needs judgment: `/code-review`, triage, and the PR text.

## When to use

- Every in-round issue is `completed` (or `ready-for-human` with its smoke test now done)
  on branch `<slug>-rN`.

## Process

If any script output has a line starting with `STOP:`, do what it says. Do not work
around it with manual git commands.

### 1. Gate on the issues (script)

```
python scripts/feature_flow.py issues
```

- Checks every in-round issue is `completed` with an `## Implementation Summary`.
- Any issue at `ready-for-human` → the script stops (exit code 3). Ask the user to run its
  Fusion smoke test. Confirmed → flip it to `completed`, commit, run again. Not confirmed →
  **stop**.
- It warns if `core/` changed but `docs/changelog.md` did not. User-visible change →
  update the changelog; bump the version in `ThreadMeister.manifest` and `manifest.json`
  if this round ships a release.

### 2. Code review (model)

Run `/code-review master...HEAD`.

### 3. Triage findings (model)

- Apply the safe, high-confidence fixes on the branch and commit them.
- File larger or uncertain findings as new issues in `.scratch/<slug>/issues/`.
- Report what was fixed vs filed.

### 4. Run the tests — once, after the review (script)

```
python scripts/feature_flow.py tests
```

Runs `python -m pytest -q` and stores the result for the current commit. Any failure →
**stop**: fix, commit, run again.

### 5. Push + open the PR (script, model writes the text)

1. Write the PR body to a file (for example `.git/pr-body.md`): `## Summary` (issues, review
   outcome fixed vs filed) and `## Merge Danger` (one-way vs two-way door, blast radius).
   Use the `pr` skill if it is installed. **Do not write `## Evidence`** — the script adds it
   from the real test run, plus the issue list.
2. Run:

```
python scripts/feature_flow.py open-pr --summary "<one line>" --body-file .git/pr-body.md
```

It sets the tracker to `awaiting-review`, commits, pushes the branch, opens (or updates) the
PR with `gh`, records the PR URL in the tracker and pushes. `open-pr` refuses to run if code
changed after the last green `tests` run.

### 6. Human checkpoint — merge on GitHub

Tell the user: *"PR <url> open. Smoke test in Fusion if needed (`scripts\deploy.bat` from the
branch). Then click **Squash and merge**."* The agent **never merges**. Review asks → push
more commits, then run `tests` and `open-pr` again.

### 7. After merge (script, when the user says it is merged)

```
python scripts/feature_flow.py after-merge
```

Checks the PR is merged, pulls `master`, sets the tracker to `merged` (a local commit on
`master`, **not pushed** — pushing `master` needs the user's approval), deletes the local
branch, and runs the tests on `master` (this repo has no CI). Red → open a revert PR and set
the tracker to `post-merge-test-failed`.

## Report

Test results, review outcome (fixed vs filed), PR URL, tracker status, next-round backlog.

## Notes

- `scripts/feature_flow.py` is identical in Track-On-Topo and ThreadMeister. Change both.
