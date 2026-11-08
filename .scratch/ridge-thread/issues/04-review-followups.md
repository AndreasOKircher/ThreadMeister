# Ridge Thread review follow-ups

Status: needs-triage

## Parent

`.scratch/ridge-thread/PRD.md`

## What to build

Findings from the r1 code review that were not fixed in r1 (uncertain or larger):

1. `core/tm_config.py`: `[Ridge Threads]` inner diameter is only checked for 0 < inner < bore. A small value (e.g. M3 = 0.3) makes the Ridge lobes overlap and every point fails with a profile error. Add a lower bound (lobes must not overlap) and a config warning, with a unit test in `tests/test_ridge.py`.
2. `core/tm_config.py`: extra sizes added by the user to `[Ridge Threads]` are silently ignored. Warn, or document it.
3. `core/tm_geometry.py` `createRidgeThreadSketch`: no guard around the dimensions/constraints; a Fusion rejection shows a generic "Failed" box. Wrap and report a clear per-point message. Needs a Fusion smoke test.
4. `core/tm_ui.py`: `RIDGE_THREAD_SPECS[size]` is indexed directly in `resetRidgeDepth` / `_ridgeInfoText`; a stale size could raise KeyError. Use `.get` with a guard.
5. `core/tm_config.py`: `save_bore_type_state` adds `[UI State]` unconditionally; check that this cannot block the old-format migration (migration normally runs first at load).

Fixed in r1 (commit after 80486ca): Ridge run now saves Hole Type and the success-message checkbox; Depth validation only for blind; `_write_config_file` keeps `last_bore_type` and `last_ridge_thread`.

## Acceptance criteria

- [ ] Each item fixed or closed with a reason.
- [ ] `python -m pytest -q` passes.

## Implementation Summary

<Filled at issue close.>
