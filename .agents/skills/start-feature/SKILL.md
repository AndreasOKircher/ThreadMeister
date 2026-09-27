---
name: start-feature
description: Start a feature round on a branch in the repo working tree. Claims the feature's issues on master (sets them on-branch, seeds the .feature-status.md tracker), then creates one branch <slug>-rN from local master where ALL of that feature's issues are implemented. Use when starting (or extending) implementation of a feature whose issues are ready-for-agent. Pairs with /finish-feature.
---

# Start Feature

Open the **one** branch where a whole feature round is implemented. One feature-slug →
one branch `<slug>-rN`, shared by every issue in that feature.

## When to use

- A feature's issues are `ready-for-agent` and you are about to implement them.
- You are **extending** a shipped feature: add new issue files to the existing
  `.scratch/<slug>/` folder, then run this to cut `<slug>-r(N+1)`.

Not for docs-only / `.scratch/` edits — those go straight to `master`.

## Inputs

- `<feature-slug>` — the `.scratch/<slug>/` folder.
- Which issues are in this round (default: every `ready-for-agent` issue in the folder).

## Process

### 0. Clean tree

`git status`. If dirty: commit, stash, or ask the user before continuing.

### 1. Pick the round number N

`git branch --list '<slug>-r*'` — first round is `r1`, an extension is the next integer.

### 2. Claim on `master` first

1. For each in-round issue, flip `Status:` from `ready-for-agent` to `on-branch`.
2. Create/update `.scratch/<slug>/.feature-status.md`:

   ```markdown
   status: in-progress
   branch: <slug>-rN
   round: N
   issues:
     - <NN>-<slug>
   ```

3. Commit on `master`:
   `git add .scratch/<slug>/ && git commit -m "start(<slug>): claim round rN -> on-branch"`

### 3. Cut the branch from local `master`

```
git checkout master && git checkout -b <slug>-rN
```

### 4. Work

Implement every issue on this branch. For each issue: `/tdd` for the Fusion-free logic,
`python -m pytest -q` green, then flip `Status: completed`, add the Implementation Summary,
and commit (one commit per issue). If an issue still needs a manual Fusion smoke test, set
`ready-for-human` instead and tell the user what to check. When all issues are done, run
`/finish-feature`.

## Report

Round number, branch name, claimed issues, and that work is now on `<slug>-rN`.
