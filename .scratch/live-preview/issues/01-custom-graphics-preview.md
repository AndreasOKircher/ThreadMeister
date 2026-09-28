# Live preview of the Bores before OK

Status: needs-triage

> **Status note.** Resolve the open questions in `../idea.md` first (`/grill-with-docs`), then set `ready-for-agent`.

## Parent

`.scratch/live-preview/idea.md`

## What to build

Handle `executePreview` or add a CustomGraphicsGroup in `core/tm_ui.py`, redrawn on
`inputChanged`, cleared on destroy.

## Acceptance criteria

- [ ] Preview appears, updates on size/type change, disappears on cancel (manual smoke).
- [ ] No preview geometry left in the design or timeline after OK or Cancel.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
