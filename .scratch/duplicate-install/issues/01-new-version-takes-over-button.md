# Newer ThreadMeister runs its own code next to an older installed copy

Status: ready-for-human
GitHub: https://github.com/AndreasOKircher/ThreadMeister/issues/1

> **Status note.** Code done and unit-tested; waiting for the manual Fusion smoke test below.

## Parent

`.scratch/duplicate-install/idea.md` — decision: ADR-0003.

## What to build

- `ThreadMeister.py`: relative imports (`from .core import …`), no `sys.path` changes.
- `core/*.py`: relative imports between modules (`from . import tm_state`,
  `from .tm_geometry import …`).
- `run()`: delete an existing `ThreadMeisterCmd` definition and toolbar control before
  `addButtonDefinition` (Autodesk pattern).
- Tests import `core.tm_*` with the repo root on `sys.path`.
- README troubleshooting entry, changelog, version 1.2.4.

### Behaviour by load order (versions ≤1.2.3 can't be changed)

| Order | Result |
|---|---|
| old copy first, 1.2.4 second | 1.2.4 removes the old button, creates its own, runs its own code |
| 1.2.4 first, old copy second | old copy shows "already exists" at startup; 1.2.4 keeps the button |

Known edge: stopping/disabling the old copy while Fusion runs calls its `stop()`, which
deletes the button by ID — 1.2.4's by then. Restarting Fusion (as the README says) restores it.

## Acceptance criteria

- [x] `python -m pytest -q` passes (64 passed, 12 skipped).
- [x] Simulation (two copies at different paths, loaded as path-named packages): each copy
      loads its own `core/tm_*.py`, no bare `tm_*` in `sys.modules`.
- [x] README troubleshooting + changelog; version 1.2.4; ADR-0003.
- [ ] Manual Fusion smoke, **only 1.2.4 installed**: add-in loads, face-sketch Bore works.
- [ ] Manual Fusion smoke, **old App Store copy + 1.2.4 both enabled at startup**, restart
      Fusion: face-sketch Bore works (no "referencePlane is a BRefFace" error).
- [ ] Text Commands check: `[k for k in sys.modules if 'tm_' in k]` shows names starting
      with `__main__…ThreadMeister_py.core.` for 1.2.4.

## Blocked by

None.

## Implementation Summary

**Code done:** 2026-09-29, branch `duplicate-install-r1`

- Relative imports throughout; nothing added to `sys.path`; existing button taken over.
- Folder-scan warning from the first commit on this branch removed again (ADR-0003,
  "Alternatives rejected").
- Tests: import paths updated; suite 64 passed, 12 skipped.
- Manual Fusion smoke: **pending**.
