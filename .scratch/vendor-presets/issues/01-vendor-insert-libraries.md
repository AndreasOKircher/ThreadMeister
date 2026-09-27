# Vendor Insert Libraries and imperial sizes

Status: needs-grill

> **Status note.** Resolve the open questions in `../idea.md` first (`/grill-with-docs`), then set `ready-for-agent`.

## Parent

`.scratch/vendor-presets/idea.md`

## What to build

Extend `core/tm_config.py` loading to read several libraries; add a vendor dropdown in
`core/tm_ui.py` that filters the Insert Size dropdown; remember the last vendor in `[UI State]`.

## Acceptance criteria

- [ ] Vendor dropdown switches the Insert Size list (manual smoke).
- [ ] Config loading tests for multiple libraries and for old configs without vendors.
- [ ] Imperial sizes present with sourced numbers.
- [ ] README documents the presets and their sources.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
