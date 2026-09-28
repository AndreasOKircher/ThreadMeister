# Bug: every run crashes when the Sketch Points lie in a sketch on a Body Face

Status: ready-for-human

> **Status note.** Code done and unit-tested; waiting for the manual Fusion smoke test listed under Verification.
GitHub: https://github.com/AndreasOKircher/ThreadMeister/issues/1

## Symptom

Clicking OK shows a traceback and no Bore is cut:

```
File "...\ThreadMeister.bundle\...\core\tm_execute.py", line 67, in notify
    face = parentSketch.referencePlane
File ".../Api/Python/packages\adsk\fusion.py", line 68638, in _get_referencePlane
    return _fusion.Sketch__get_referencePlane(self)
RuntimeError: 3 : referencePlane is a BRefFace - need to roll timeline back before sketch
```

Expected: one Bore per Sketch Point, as in March 2026.

## Reproduction

1. New design. Sketch a rectangle on XY, extrude it.
2. Create a sketch **on the top face** of the extrusion, place a point.
3. Run ThreadMeister, select the body and the point, OK → error above.

Control: the same point in a sketch on the XY plane, or on an offset plane (offset 0) placed
on the face → works.

## Root cause (locked 2026-09-27)

`core/tm_execute.py:68` reads `parentSketch.referencePlane` to place the Temp Sketch
(ADR-0001). A Fusion update after March 2026 made that property raise for sketches on a
Body Face when the timeline marker is past the sketch — even with nothing after the sketch.
The code is unchanged since v1.2.0 (verified then); only Fusion's behaviour changed.
Autodesk forum: "Sketch.referencePlane property functionality changed". Decision: ADR-0002.

## Fix

Per ADR-0002, in a new helper in `core/tm_geometry.py` (e.g. `resolveSketchPlane(parentSketch, targetBody)`):

1. `try: return parentSketch.referencePlane` — unchanged path for construction planes.
2. On exception: origin + normal from `parentSketch.transform.getAsCoordinateSystem()`;
   scan for a planar face whose plane contains the origin and whose outward normal is
   parallel to the sketch normal (prefer same direction). Search `targetBody.faces` first,
   then the faces of the other bodies in `targetBody.parentComponent.bRepBodies` — the
   Parent Sketch may sit on a face of a different body than the one being cut (this worked
   in v1.2.0 and must keep working). Return the first match.
3. None found → return `None`; `tm_execute.py` fails that point with
   "Point N: could not find the sketch's face." and continues.

In `core/tm_execute.py`:

- Use the helper instead of line 68.
- Keep `direction` exactly as today (computed from the Parent Sketch). It is also passed to
  `findDistanceThroughBody()` (`tm_execute.py:124`), which interprets it against the Parent
  Sketch's axis (`tm_geometry.py:436`) — so `direction` itself must **not** be flipped.
- Add a separate `cutDirection` for the extrude only: after `addWithoutEdges`, compare the
  Temp Sketch normal with the Parent Sketch normal; `cutDirection` = `direction` if they
  match, the opposite enum value if not. Pass `cutDirection` to `setOneSideExtent()`
  (both the blind and the through branch).

Not changed: how `direction` is computed, through-distance and chamfer logic (still use the
Parent Sketch's transform).

## Verification

- Unit tests (mocked faces) for the face lookup: coplanar same normal → found; coplanar
  opposite normal → found as fallback; parallel but offset plane → rejected; face only on
  another body in the component → found; no planar face → `None`; `referencePlane` works →
  returned untouched.
- Unit test for `cutDirection`: same normals → unchanged, opposite normals → flipped, and
  `direction` passed to `findDistanceThroughBody` is never flipped.
- Manual Fusion smoke (deploy with `scripts\deploy.bat`):
  - point in sketch on a Body Face → Bore cut, blind and through;
  - point in sketch on XY plane → still works;
  - point in sketch on an offset plane → still works;
  - Chamfer + Bottom Radius on the face case;
  - several points from two sketches on different faces in one run;
  - sketch on a face of body A, Target Body B (Bore goes into B).

## Out of scope

- The timeline-rollback workaround from the forum (possible later fallback, ADR-0002).
- Shared Temp Sketch per Parent Sketch.

## Evidence

- GitHub issue #1 (reporter screenshot).
- Maintainer repro 2026-09-27: XY plane works, face fails, construction plane on face works.

## Blocked by

None — can start immediately.

## Implementation Summary

**Code done:** 2026-09-28, branch `reference-plane-fix-r1` (commit that flipped this issue to `ready-for-human`)

- `core/tm_geometry.py`: `resolveSketchPlane()` reads `referencePlane` and, if Fusion
  raises, falls back to `findFaceForSketchPlane()`. That searches the Target Body, then the
  component's other bodies, for a planar face in the sketch plane (same normal preferred).
  `alignExtrudeDirection()` flips the extrude direction for the cut only when the Temp
  Sketch's normal is opposite to the Parent Sketch's.
- `core/tm_execute.py`: uses both; `direction` for `findDistanceThroughBody` is unchanged;
  no face found → per-point failure message instead of a traceback.
- Tests: 14 new unit tests in `tests/test_sketch_plane.py`; suite 64 passed, 12 skipped.
- Not unit-testable: `tm_execute.py` can't be imported under the `adsk` mock (its handler
  subclasses a mocked Fusion class), so the "`direction` passed to `findDistanceThroughBody`
  is never flipped" check is covered by the through-hole smoke test instead.
- Assumption to confirm in Fusion: `addWithoutEdges()` accepts the face found at the end of
  the timeline, and `BRepFace.evaluator.getNormalAtPoint()` returns the outward normal.
- Manual Fusion smoke: **pending**.
