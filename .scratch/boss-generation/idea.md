# boss-generation

The most common use of inserts in 3D printing is mounting posts inside enclosures. A
"Create boss" checkbox could extrude a cylinder at each Sketch Point before cutting the Bore:
diameter = hole diameter + 2 × Minimum Wall Thickness (reuses the currently unused Insert Spec
value). Goes from a bare Sketch Point to a finished post in one run.

Earlier analysis (session "Feature proposals for repo", 2026-06-11): add a boss height input
with two modes — fixed distance, or "to object" (up to a selected face) — plus validation.

## Open questions

- Height: fixed distance, up-to-face, or both? Default height?
- Direction: the boss grows away from the body (outside) or into empty space inside an enclosure — how is that decided?
- Join the boss to the Target Body, or create a new body?
- Optional fillet at the boss base?
- How does this interact with Blind vs Through Hole?

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
