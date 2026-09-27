# through-all-extent

The README lists through-hole instability as a known limitation. Today a Through Hole is a
one-sided **distance** cut: `findDistanceThroughBody()` (`core/tm_geometry.py:421`) steps along
the normal in 1 mm steps with `pointContainment` and adds 2 mm (`core/tm_execute.py:123-127`).
Missed exits or thin walls give partial cuts. Fusion's `ThroughAllExtentDefinition` would let
Fusion cut through the whole body and remove the distance code path.

## Open questions

- Does Through All with `participantBodies = [targetBody]` also cut other bodies? (It shouldn't — verify in Fusion.)
- Is the old distance path still needed as a fallback when Through All fails?
- Chamfer on the exit side too, or entry only (as now)?

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
