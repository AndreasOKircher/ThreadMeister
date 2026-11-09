# Warn when a Bore hangs over the face edge

Status: needs-triage

## Parent

`.scratch/live-preview/idea.md`. Found in the smoke test of `issues/01-custom-graphics-preview.md` (2026-11-09).

## What to build

A Sketch Point near an outside or inside corner of the face gets a partial Bore. Today this counts as "created" in the OK message. Only a point with no usable face fails ("Could not determine extrusion direction").

- After a Bore is cut in `runBores` (`core/tm_execute.py`), detect that the circle does not fit on the entry face (e.g. compare the removed volume with the expected cylinder volume, or check the circle against the face boundary).
- Add a warning line per point to `result.warnMessages`: `Point N: Bore only partly inside the face.` The Bore stays.
- The preview stays silent (D4 of issue 01).

Open question: which check is robust on curved or slanted entry faces? Decide before coding.

## Acceptance criteria

- [ ] A point at an outside corner and a point at an inside corner each give a warning on OK (manual smoke).
- [ ] A normal Bore gives no warning (manual smoke).
- [ ] Unit test for any pure maths (e.g. volume ratio).
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

`issues/01-custom-graphics-preview.md` (shares `runBores`).

## Implementation Summary

<Filled at issue close.>
