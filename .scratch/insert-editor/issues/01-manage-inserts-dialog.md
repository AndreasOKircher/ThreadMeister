# "Manage inserts…" dialog

Status: needs-grill

> **Status note.** Resolve the open questions in `../idea.md` first (`/grill-with-docs`), then set `ready-for-agent`.

## Parent

`.scratch/insert-editor/idea.md`

## What to build

New command/dialog in `core/`; writes through `core/tm_config.py` (reuse
`_write_config_file`). Validation logic as pure functions with unit tests.

## Acceptance criteria

- [ ] Add, edit, delete an insert; the main dropdown reflects it (manual smoke).
- [ ] Unit tests for validation and for config write/read round-trip.
- [ ] Invalid input can't corrupt `config.ini`.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
