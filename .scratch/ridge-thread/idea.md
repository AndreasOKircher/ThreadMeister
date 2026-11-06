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

## Test results

2026-10-15, user's own print tests, M3 / M4 / M5, fork default parameters vs. ridge diameter
+0.2 mm (arc distance unchanged):

- +0.2 mm ridge diameter gave higher strength, clearly at least for M3. M4 / M5: not yet clear.
- Effect of +0.2 with the same arc distance: each ridge reaches 0.1 further in, so the inner
  diameter at the ridges drops by 0.2 (calculated from the fork's table, research.md Q3):

  | Size | Inner Ø default | Inner Ø +0.2 | Tap drill (D−P) | D1 | D2 |
  |---|---|---|---|---|---|
  | M3 | 2.60 | 2.40 | 2.50 | 2.459 | 2.675 |
  | M4 | 3.50 | 3.30 | 3.30 | 3.242 | 3.545 |
  | M5 | 4.50 | 4.30 | 4.20 | 4.134 | 4.480 |

- So the stronger M3 version sits below the tap drill, near D1, not at D2. That matches Roland
  Smith's M3 crush ribs (ridges down to Ø2.4, research.md Q2).
- Setup: ASA, 3 perimeters, 0.2 mm layer height. Layers at 90° to the bore axis (bore printed
  vertically), so the layers run roughly parallel to the thread.
- Still to record: test method, numbers. Horizontal bores not tested yet.

2026-10-18, user's second test round, PETG, same two variants (inner Ø −0.2 mm vs. default):

- M3: inner Ø −0.2 (2.40) is fine.
- M4 / M5: inner Ø −0.2 (3.30 / 4.30) is too small. Too much friction when the screw goes in.
- So the −0.2 step does not scale to M4 / M5 (at least in PETG). These sizes need a value
  between default and −0.2, or the default. Not yet tested.

### Decision (2026-11-07, user reviewed both rounds)

| Size | Inner Ø at ridges | Ridges | Source |
|---|---|---|---|
| M3 | 2.40 | 3 | default −0.2 (ridge Ø +0.2, arc distance unchanged) |
| M4 | 3.50 | 3 | fork default, no change |
| M5 | 4.50 | 4 | fork default, no change |

Printer: Prusa Core One. Filaments: Prusament ASA and Prusament PETG. Layer height assumed 0.2 mm.

### Decisions (2026-11-07)

- **Lead-in:** same as ThreadMeisterExtended: distance-and-angle chamfer on the top edge of each
  ridge arc, 78°, fork's per-size chamfer distance.
  Open check: M3 protrusion is now 0.40 (was 0.30), but the fork chamfer is 0.28. Keep 0.28, or
  follow the fork rule "chamfer ≈ protrusion − a little" (≈ 0.38)?
- **Depth:** default 4 × D (M3 = 12, M4 = 16, M5 = 20). Depth is the only Ridge Thread value the
  user can edit in the dialog.
- **config.ini:** each Ridge Thread size gets one parameter, the inner diameter at the ridges,
  plus a comment line that says what this diameter is.
- **Name:** user asked "grip ridge" vs "ridge thread" — see answer in session; add the chosen term
  to `CONTEXT.md`.

## Open questions

- ~~Size rule~~ Decided 2026-11-07 from tests: M3 inner Ø 2.40 (default −0.2); M4 3.50 and
  M5 4.50 (fork defaults, unchanged).
- ~~Ridge count~~ Decided 2026-11-07: M3 / M4 = 3, M5 = 4 (same as the fork defaults that were tested).
- ~~Which sizes to ship~~ Decided 2026-11-07: M3, M4, M5 only. Other sizes are not needed.
- Credit: README note for Thomas Sanladerer and Connor McComb; ask Connor where the non-M3
  numbers come from (questions at the end of research.md).

Source: session "ThreadMeisterExtended analysis" (2026-10-15). Tests being prepared by the user
in parallel.
