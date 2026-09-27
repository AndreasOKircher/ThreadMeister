# Insert shopping list from the timeline

Status: needs-triage

> **Status note.** Resolve the open questions in `../idea.md` first (`/grill-with-docs`), then set `ready-for-agent`.

## Parent

`.scratch/insert-bom/idea.md`

## What to build

New small command that walks `design.timeline.timelineGroups` and parses names (pure
parser with unit tests), or reads attributes if decided.

## Acceptance criteria

- [ ] Counts match a test design with several runs (manual smoke).
- [ ] Unit tests for the name parser, including renamed/unknown groups.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
