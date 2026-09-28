# Optional boss (mounting post) under each Bore

Status: needs-grill

> **Status note.** Resolve the open questions in `../idea.md` first (`/grill-with-docs`), then set `ready-for-agent`.

## Parent

`.scratch/boss-generation/idea.md`

## What to build

New dialog group "Boss" in `core/tm_ui.py` (checkbox + height). In `core/tm_execute.py`,
before the Bore cut, extrude a join cylinder from the Temp Sketch (second circle, diameter
from the Insert Spec). Bore depth logic unchanged.

## Acceptance criteria

- [ ] Boss + Bore created in one run, inside the Timeline Group (manual smoke).
- [ ] Boss diameter = hole diameter + 2 × min wall (unit test for the maths).
- [ ] Height validation in `ValidateInputsHandler`.
- [ ] README/help.html document the option.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
