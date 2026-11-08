# PRD: Ridge Thread

Date: 2026-11-07. Source: `idea.md` (all decisions), `research.md` (dimension research).

## Problem

Users want screw holes in printed parts without heat-set Inserts: fast to model, good enough
for low and medium load. ThreadMeister only cuts Insert Bores today.

## Solution

A second Bore type, **Ridge Thread**: a bore a little larger than the screw, with N arc-shaped
ridges that stick into the bore. The screw forms its own thread in the ridges. Concept by
Thomas Sanladerer; first Fusion version in Connor McComb's fork ThreadMeisterExtended (there
called "Grip Ridge"). Both are credited in the Readme.

## User stories

1. As a user, I pick "Ridge Thread" in a Bore Type dropdown, then M3, M4 or M5, then Blind or
   Through, and ThreadMeister cuts one Ridge Thread at each selected Sketch Point.
2. As a user, I can change the depth of a blind Ridge Thread in the dialog. The default is
   4 × screw diameter.
3. As a user, when I move the Sketch Point later, the Ridge Thread moves with it.
4. As a user, the ridges have a lead-in chamfer, so the screw starts easily.
5. As a power user, I can tune the inner diameter at the ridges for each size in `config.ini`.

## Decisions

| Size | Inner Ø at ridges (config.ini) | Ridges | Bore Ø | Arc distance | Lead-in chamfer | Default depth |
|---|---|---|---|---|---|---|
| M3 | 2.40 | 3 | 3.2 | 2.05 | 0.28 | 12 |
| M4 | 3.50 | 3 | 4.2 | 2.75 | 0.33 | 16 |
| M5 | 4.50 | 4 | 5.3 | 3.50 | 0.37 | 20 |

- Only M3, M4, M5. Values from the user's print tests (Prusa Core One, Prusament ASA and PETG,
  0.2 mm layers): M3 = fork default −0.2, M4 / M5 = fork default.
- Bore Ø, arc distance (hole axis → ridge-circle centre), ridge count and chamfer are built in
  (fork values). Ridge-circle Ø is derived: `ridge_dia = 2 × arc_distance − inner_dia`
  (M3: 1.7, M4: 2.0, M5: 2.5). So a smaller inner Ø makes the ridges bigger, with the arc
  distance unchanged — the same way the user's M3 test part was made.
- `config.ini` gets a new section `[Ridge Threads]` with one value per size (inner Ø) and a
  comment line that says what the value means.
- Lead-in: same as the fork: distance-and-angle chamfer, 78°, on the top edge of each ridge arc.
- Dialog: "Bore Type" dropdown above "Insert Size" (Heat-Set Insert / Ridge Thread), with an
  icon per item, same as the fork. Ridge Thread → size list M3 / M4 / M5, Depth field shown
  (blind only), Chamfer and Bottom Radius hidden. Depth is the only Ridge Thread value the user
  edits in the dialog. It resets to 4 × D when the size changes; it is not remembered.
- Icons: copy the fork's `resources/icons/heatset` and `resources/icons/gripridge` icons for
  now (MIT, keep Connor McComb's copyright notice). An own icon is a later issue.
- Sketch: unlike the fork, every Ridge Thread curve is constrained to the projected Sketch
  Point (fork bug: the ridges stayed behind when the point moved). No trim step.

## Out of scope

- Other sizes (M1.6–M2.5, M6+). Editing ridge count, bore Ø or chamfer in the dialog.
- Own icon design. Horizontal-bore print tests.
- Through-hole depth that updates when the point moves (same limit as Insert Bores today).

## Issues

1. `issues/01-ridge-thread-bore.md` — Bore Type dropdown, config, constrained sketch, cut.
2. `issues/02-ridge-lead-in-chamfer.md` — 78° chamfer on the ridge top edges.
3. `issues/03-icons-docs-credit.md` — dropdown icons, Readme / help / changelog, credits.
