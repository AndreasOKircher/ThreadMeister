# Bug: every run crashes when the Sketch Points lie in a sketch on a Body Face

Status: ready-for-agent
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
   scan `targetBody.faces` for a planar face whose plane contains the origin and whose
   outward normal is parallel to the sketch normal (prefer same direction). Return it.
3. None found → return `None`; `tm_execute.py` fails that point with
   "Point N: could not find the sketch's face on the target body." and continues.

In `core/tm_execute.py`:

- Use the helper instead of line 68.
- After `addWithoutEdges`, compare the Temp Sketch normal with the Parent Sketch normal; if
  opposite, flip `direction` (it is computed from the Parent Sketch).

Not changed: Extrude Direction, through-distance and chamfer logic (still use the Parent
Sketch's transform).

## Verification

- Unit tests (mocked faces) for the face lookup: coplanar same normal → found; coplanar
  opposite normal → found as fallback; parallel but offset plane → rejected; no planar face
  → `None`; `referencePlane` works → returned untouched.
- Manual Fusion smoke (deploy with `scripts\deploy.bat`):
  - point in sketch on a Body Face → Bore cut, blind and through;
  - point in sketch on XY plane → still works;
  - point in sketch on an offset plane → still works;
  - Chamfer + Bottom Radius on the face case;
  - several points from two sketches on different faces in one run.

## Out of scope

- The timeline-rollback workaround from the forum (possible later fallback, ADR-0002).
- Shared Temp Sketch per Parent Sketch.

## Evidence

- GitHub issue #1 (reporter screenshot).
- Maintainer repro 2026-09-27: XY plane works, face fails, construction plane on face works.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
