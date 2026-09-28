# reference-plane-fix

GitHub issue #1 (brownem, 2026-09-27): "Runtime Error 3: Reference Plane is a Bref Face -
need to roll timeline back before sketch". Every run fails when the Sketch Points sit in a
sketch placed directly on a Body Face.

## Findings (2026-09-27)

- Error comes from reading `parentSketch.referencePlane` (`core/tm_execute.py:68`), not
  from `addWithoutEdges`.
- Reproduced with the simplest timeline: sketch → extrude → sketch on the new face.
- XY-plane sketch works. Sketch on a construction plane placed on the face works.
- Code unchanged since v1.2.0, which was built for and verified on face sketches → Fusion
  changed the property's behaviour. Confirmed by the Autodesk forum thread
  "Sketch.referencePlane property functionality changed".
- Forum workaround (roll timeline back, read, roll forward) rejected as primary fix — see
  ADR-0002.

## User workaround (confirmed)

Create an offset plane (offset 0) on the face, draw the sketch on that plane.
