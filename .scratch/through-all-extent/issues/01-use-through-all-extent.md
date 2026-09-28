# Cut Through Holes with Fusion's Through All extent

Status: needs-triage

> **Status note.** Resolve the open questions in `../idea.md` first (`/grill-with-docs`), then set `ready-for-agent`.

## Parent

`.scratch/through-all-extent/idea.md`

## What to build

Replace the distance extent in the Through Hole branch of `core/tm_execute.py:123-127` with
`adsk.fusion.ThroughAllExtentDefinition.create()` plus the computed direction. Remove
`findDistanceThroughBody()` if nothing else uses it. Update the README limitation section.

## Acceptance criteria

- [ ] Through Hole on a thick and a thin-walled part cuts fully in Fusion (manual smoke).
- [ ] Only the Target Body is cut when other bodies overlap the Bore.
- [ ] `findDistanceThroughBody` removed or still justified in the issue.
- [ ] README "Known Technical Limitations" updated.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
