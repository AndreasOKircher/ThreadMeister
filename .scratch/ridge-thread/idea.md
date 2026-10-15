# ridge-thread

Add a "ridge thread" hole type: a bore slightly larger than the screw, with N arc-shaped ridges
protruding inward. The screw forms its own thread in the ridges, so no heat-set insert is needed.
Concept by Thomas Sanladerer (Made With Layers); first Fusion implementation in Connor McComb's
fork [ThreadMeisterExtended](https://github.com/kiwimccomb-maker/ThreadMeisterExtended) ("Grip
Ridge"). Dimension research: [research.md](research.md).

## User need

- Screw holes in printed parts without inserts, fast to model, good enough for low/medium load.
- Simple dialog: pick body, points, type, size, blind/through. Defaults come from `config.ini`;
  the ridge geometry is not edited in the dialog (the fork shows ~8 extra fields for it).
- The hole must follow its Sketch Point when the point moves later.

## Notes from the fork

- Association bug: the fork draws the ridge circles at fixed coordinates in the temp sketch and
  never constrains them to the projected point (`create_grip_ridge_sketch` in
  `core/tm_geometry.py`), so moving the point leaves the hole behind. The standard hole path
  does constrain the circle centre (coincident). Fix: constrain everything to the projected
  point (centre coincident, construction lines to ridge centres with length + angle, diameters)
  and drop the trim step — the central profile is the same without it.
- Through-hole depth is a fixed number measured once; it does not update when the point moves
  (same for standard holes).

## Open questions

- Size rule: inner diameter at the ridges ≈ pitch diameter D2 (what the fork's table does), or
  test-based values per size? See research.md, Q3. Only M3 has a public source (Thomas's model).
- Ridge count: always 3 (Thomas; easy "one ridge down" print orientation) or more above M4?
- Lead-in: chamfer on the ridge top edges (fork, 78°) or a swept taper (Thomas, 0.3 × 1.5)?
- Default depth per size?
- Which sizes to ship: Thomas only recommends this up to M5.
- Credit: README note for Thomas Sanladerer and Connor McComb; ask Connor where the non-M3
  numbers come from (questions at the end of research.md).

Source: session "ThreadMeisterExtended analysis" (2026-10-15). Tests being prepared by the user
in parallel.
