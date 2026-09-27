# Screw clearance holes in the mating part

Status: needs-grill

> **Status note.** Resolve the open questions in `../idea.md` first (`/grill-with-docs`), then set `ready-for-agent`.

## Parent

`.scratch/clearance-holes/idea.md`

## What to build

Optional second body selection in `core/tm_ui.py`; for each point, a Through All cut of the
clearance diameter into that body. Depends on through-all-extent.

## Acceptance criteria

- [ ] Clearance holes line up with the Bores (manual smoke).
- [ ] Clearance size lookup unit-tested.
- [ ] README documents the option.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

`.scratch/through-all-extent/issues/01-use-through-all-extent.md`

## Implementation Summary

<Filled at issue close.>
