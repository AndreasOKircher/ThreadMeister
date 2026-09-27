# ADR-0001: Draw each Bore circle in a clean Temp Sketch

Status: accepted (v1.2.0, 2026-03-14)

## Context

Up to v1.1.x ThreadMeister drew the Bore circle directly in the Parent Sketch and then
searched that sketch's profiles for the one matching the circle. When a sketch lies on a
Body Face, Fusion automatically projects the body's edges into it. Those projected curves
split the Bore profile unpredictably, so profile selection (`findProfileForCircle`) failed
on real parts even after a four-stage filter chain.

## Decision

For each Sketch Point, create a new **Temp Sketch** on the same Sketch Plane with
`component.sketches.addWithoutEdges(plane)`, which creates a sketch without projected body
edges. Project the Sketch Point into it (keeps the parametric link), draw the Bore circle,
and cut from that sketch. The Parent Sketch is never modified.

## Consequences

- The Temp Sketch holds only the projected point and the circle → exactly two profiles,
  profile selection is trivial.
- One extra sketch per Bore in the timeline (named `TM_<insert>_P<n>`, inside the Timeline
  Group). A shared Temp Sketch per Parent Sketch is a possible later optimisation.
- ThreadMeister needs the Parent Sketch's plane. v1.2.0 read it from
  `Sketch.referencePlane` — superseded for Body Faces by ADR-0002.

## Alternatives rejected

- **Keep drawing in the Parent Sketch** — root cause of the failures.
- **Rebuild loops from a 2D curve graph** — much more code; kept as a fallback idea in
  `docs/development-notes.md`.
