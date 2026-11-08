# Ridge Thread lead-in chamfer

Status: ready-for-human

## Parent

`.scratch/ridge-thread/PRD.md`

## What to build

After the Ridge Thread cut (issue 01), chamfer the top edge of each ridge arc at the bore
entry, same as ThreadMeisterExtended: distance-and-angle chamfer, 78° from the face plane,
distance per size M3 0.28 / M4 0.33 / M5 0.37 (built in, not in `config.ini`). Always on for
Ridge Thread (no checkbox).

- Port `getGripRidgeChamferEdges` and `addAngleChamferToEdge` from
  `../ThreadMeisterExtended/core/tm_geometry.py` into `core/tm_geometry.py`, renamed to
  Ridge Thread terms. Keep its edge filter: arc radius = ridge radius, arc centre at the arc
  distance from THIS bore's axis, edge in the sketch plane (top edges only).
- Uses the Temp Sketch transform, not `Sketch.referencePlane` (ADR-0002).
- If no edges are found or the chamfer fails: keep the bore, add a per-point warning to the
  result message (do not fail the point).
- Note: M3 ridges now stick out 0.40 but the chamfer stays 0.28 (user decision, tested).

## Acceptance criteria

- [x] Unit test for any pure edge-filter maths that can run without Fusion.
- [x] `python -m pytest -q` passes.
- [ ] Manual Fusion smoke: M3 / M4 / M5 blind and through — each ridge top edge has the
      chamfer; bottom edges of a through hole and other Ridge Threads in the body are not
      chamfered.
- [ ] Manual Fusion smoke: the chamfer survives moving the Sketch Point.

## Blocked by

`.scratch/ridge-thread/issues/01-ridge-thread-bore.md`

## Implementation Summary

Added `is_ridge_top_edge` and `CHAMFER_ANGLE_DEG` to `core/tm_ridge.py` (pure, unit-tested in `tests/test_ridge.py`). Added `getRidgeChamferEdges` and `addAngleChamferToEdge` to `core/tm_geometry.py` (Temp Sketch transform, no `referencePlane`). `core/tm_execute.py` chamfers after the Ridge cut; on failure the bore stays and a warning is added to the result message. Chamfer distance per size comes from the existing `RidgeGeometry.chamfer`. Fusion smoke test still open.
