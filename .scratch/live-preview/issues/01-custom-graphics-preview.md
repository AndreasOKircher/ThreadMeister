# Live preview of the Bores before OK

Status: needs-triage

> **Status note.** Resolve the open questions in `../idea.md` first (`/grill-with-docs`), then set `ready-for-agent`.

## Parent

`.scratch/live-preview/idea.md`

## What to build

Handle `executePreview` in `core/tm_ui.py`. In it, build one temporary body per Bore with
`TemporaryBRepManager` and draw it in a CustomGraphicsGroup: red, translucent (opacity ~0.4).
Clear the group on each redraw and on destroy. See the 2026-11-09 decision in `../idea.md`.

## Acceptance criteria

- [ ] Translucent red Bores appear when body + Sketch Points are selected (manual smoke).
- [ ] Preview appears, updates on size/type change, disappears on cancel (manual smoke).
- [ ] No preview geometry left in the design or timeline after OK or Cancel.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
