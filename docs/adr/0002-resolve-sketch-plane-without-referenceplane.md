# ADR-0002: Resolve the Sketch Plane without `referencePlane` for Body Faces

Status: accepted (2026-09-27) — implementation: `.scratch/reference-plane-fix/`

## Context

ADR-0001 creates each Temp Sketch on `parentSketch.referencePlane`. After March 2026 a
Fusion update changed `Sketch.referencePlane`: for a sketch that lies on a Body Face, reading
the property at the end of the timeline now raises

```
RuntimeError: 3 : referencePlane is a BRefFace - need to roll timeline back before sketch
```

Construction planes (origin planes, offset planes) still work. Reported as GitHub issue #1
and reproduced 2026-09-27 with the simplest timeline (sketch → extrude → sketch on the new
face). Autodesk forum thread: "Sketch.referencePlane property functionality changed".

## Decision

1. Keep reading `referencePlane` first — it still works for construction planes.
2. If it raises, don't touch the timeline. Take the plane from the Parent Sketch's own
   geometry (`sketch.transform` → origin + normal) and find the planar face of the Target
   Body, as it is **now**, that lies in that plane with the same outward normal. Create the
   Temp Sketch on that face.
3. After creating the Temp Sketch, compare its normal with the Parent Sketch's normal and
   flip the Extrude Direction if they are opposite.
4. If no face matches, fail that Sketch Point with a clear message instead of a traceback.

## Alternatives rejected

- **Roll the timeline back before the sketch, read `referencePlane`, roll forward** (the
  workaround posted on the Autodesk forum). Recomputes the model twice per Sketch Point
  (slow on big parts), leaves the marker moved if anything fails mid-way, and the face
  obtained in the rolled-back state may itself be rejected by `addWithoutEdges` at the end
  of the timeline. Kept only as a possible last-resort fallback.
- **Always sketch on a construction plane created by the add-in.** In a parametric design
  the plane needs a face reference too, so it hits the same problem.

## Consequences

- Behaviour no longer depends on how Fusion treats `referencePlane` for faces.
- New helper (face lookup by plane) is pure geometry on sketch/body data and can be unit
  tested with mocks.
- Don't add new `referencePlane` calls (noted in `AGENTS.md` Gotchas).
