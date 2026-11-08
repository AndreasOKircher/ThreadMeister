---
name: start-feature
model: haiku
description: Start a feature round on a branch in the repo working tree. Runs scripts/feature_flow.py, which creates one branch <slug>-rN from up-to-date origin/master (or keeps the cloud session's claude/… branch), then claims the feature's issues in the branch's first commit (sets them on-branch, seeds the .feature-status.md tracker). ALL of that feature's issues are implemented on that branch. Use when starting (or extending) implementation of a feature whose issues are ready-for-agent. Pairs with /finish-feature.
---

# Start Feature

Open the **one** branch where a whole feature round is implemented. One feature-slug →
one branch `<slug>-rN`, shared by every issue in that feature.

**All mechanical steps are in `scripts/feature_flow.py`. Do not repeat them by hand.**

## When to use

- A feature's issues are `ready-for-agent` and you are about to implement them.
- You are **extending** a shipped feature: add new issue files to the existing
  `.scratch/<slug>/` folder, then run this to cut `<slug>-r(N+1)`.

Not for docs-only / `.scratch/` edits — those go straight to `master`.

## Inputs

- `<feature-slug>` — the `.scratch/<slug>/` folder.
- Which issues are in this round (default: every `ready-for-agent` issue in the folder).

## Process

### 1. Run the script

```
python scripts/feature_flow.py start <slug>
python scripts/feature_flow.py start <slug> --issues 01-a 02-b    # only some issues
```

It checks that no tracked file is dirty, picks the round number N (tracker + existing
branches), cuts `<slug>-rN` from up-to-date `origin/master` (cloud session: keeps the
`claude/…` branch), flips the issues to `on-branch`, writes `.feature-status.md`
(an earlier round becomes a history section) and makes the claim commit
`start(<slug>): claim round rN -> on-branch` **on the branch**.

If the output has a line starting with `STOP:`, do what it says (a dirty tree means
ask the user: commit, stash, or abort) and run the script again. Never work around it
with manual git commands.

### 2. Report

Show the user the script's output: round number, branch, claimed issues.

### 3. Work

Implement every issue on this branch. For each issue: `/tdd` for the Fusion-free logic,
`python -m pytest -q` green, then add the Implementation Summary and commit (one commit per
issue). Status in that commit: `completed` if nothing is left to check; `ready-for-human` if a
manual Fusion smoke test is still open — tell the user what to check. When all issues are
done, run `/finish-feature`.

## Notes

- `scripts/feature_flow.py` is identical in Track-On-Topo and ThreadMeister. Change both.
