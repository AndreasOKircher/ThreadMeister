# Ridge Thread Bore: Bore Type dropdown, config and constrained cut

Status: ready-for-human

## Parent

`.scratch/ridge-thread/PRD.md` (decisions table there).

## What to build

End-to-end Ridge Thread without the lead-in chamfer (that is issue 02).

1. **Config** (`core/tm_config.py`, `config.ini`): new section `[Ridge Threads]`,
   `M3 = 2.40`, `M4 = 3.50`, `M5 = 4.50`, with a comment line above:
   `# Inner diameter at the ridges in mm (the screw forms its thread in the ridges)`.
   Load into a new `tm_state.RIDGE_THREAD_SPECS`. Missing section / missing size → built-in
   default. Invalid value (not a number, or not between 0 and the size's bore Ø) → warning
   and default, same style as `[Inserts]`. Add the section to `create_default_config()` and
   to the migration path so existing user configs get it.
2. **Pure logic** (new functions in `core/tm_helpers.py` or a new `core/tm_ridge.py`):
   - Built-in table per size: bore Ø, arc distance, ridge count, chamfer (PRD table).
   - `ridge_dia = 2 × arc_distance − inner_dia`.
   - Default depth `4 × D`.
   - Expected area of the central profile: bore circle minus N circle–circle lens areas.
     Used to pick the right profile.
3. **Dialog** (`core/tm_ui.py`): "Bore Type" dropdown above "Insert Size" with
   "Heat-Set Insert" and "Ridge Thread" (text only here; icons come in issue 03). Ridge Thread
   → Insert Size lists M3 / M4 / M5, a "Depth" value input appears (blind only, default
   4 × D, reset on size change), Chamfer and Bottom Radius are hidden. Info text shows the
   Ridge Thread values. Remember the last Bore Type in `[UI State]`.
4. **Execute** (`core/tm_execute.py`): Ridge Thread branch in the per-point loop. In the
   Temp Sketch (named `TM_<size> Ridge Thread_P<n>`):
   - bore circle, centre coincident to the projected point (as today);
   - N ridge circles, each centre at the end of a construction line from the projected point,
     with length = arc distance and angle 360°/N × i (first ridge on the sketch x axis, as the
     fork), plus diameter dimensions. Moving the Sketch Point must move everything.
   - No trim. Pick the central profile by expected area + centroid at the point.
   - Cut blind (dialog depth) or through (`findDistanceThroughBody`), same direction logic as
     Insert Bores. Timeline Group `(<count>x <size> Ridge Thread)`.

Not changed: Insert Bore behaviour. No new `Sketch.referencePlane` calls (ADR-0002).
`CONTEXT.md`: add **Ridge Thread**, **Ridge**, **Bore Type**.

Reference only (do not copy the trim / fixed-coordinate approach):
`../ThreadMeisterExtended/core/tm_geometry.py` `create_grip_ridge_sketch`.

## Acceptance criteria

- [ ] Unit tests: `[Ridge Threads]` parsing (valid, missing, invalid → default), ridge Ø
      formula (M3 1.7, M4 2.0, M5 2.5), default depth (12 / 16 / 20), central profile area.
- [ ] Existing configs without `[Ridge Threads]` still load; the section is added.
- [ ] `python -m pytest -q` passes.
- [ ] Manual Fusion smoke: M3 / M4 / M5, blind and through, on a construction-plane sketch and
      on a body-face sketch. Cross-section shows 3 / 3 / 4 ridges, inner Ø 2.40 / 3.50 / 4.50.
- [ ] Manual Fusion smoke: move the Sketch Point afterwards → the Ridge Thread follows.
- [ ] Manual Fusion smoke: Insert Bores still work as before.
- [ ] `docs/changelog.md` entry (Unreleased).

## Blocked by

None — can start immediately.

## Implementation Summary

**Code done:** 2026-11-07, on `ridge-thread-r1` (TDD). Manual Fusion smoke still open.

- New `core/tm_ridge.py`: built-in size table (M3 / M4 / M5), `ridge_geometry()` (Ridge Ø =
  2 × arc distance − inner Ø, default depth 4 × D), `central_profile_area_mm2()`.
- `config.ini` `[Ridge Threads]` with comment line; loaded into `tm_state.RIDGE_THREAD_SPECS`,
  bad values → default + warning, missing section appended to the user's file. `[UI State]`
  remembers `last_bore_type` and `last_ridge_thread`. `_read_config_file` now keeps `#` lines,
  so the save_* functions no longer delete comments.
- Dialog: Bore Type dropdown, size list switches, Depth field (blind only, reset to 4 × D on
  size change), Chamfer / Bottom Radius hidden for Ridge Thread.
- Execute: `createRidgeThreadSketch()` draws bore + Ridge circles, all constrained to the
  projected point (construction lines with length + angle dimensions, first line horizontal,
  diameter dimensions); no trim; central profile picked by area. Timeline Group
  `(Nx M3 Ridge Thread)`.
- `CONTEXT.md` (Bore Type, Ridge Thread, Ridge), `docs/development-notes.md`, changelog.
- Tests: 13 in `tests/test_ridge.py`, 12 in `tests/test_config.py::TestRidgeThreadConfig`.
  All 137 tests pass.
- Manual Fusion smoke: **not done yet** (acceptance criteria above).
