# Grip ridge (self-forming thread) hole dimensions: where do the numbers come from?

Research date: 2026-10-15. All lengths are in mm.

Context: done in a local clone of [ThreadMeisterExtended](https://github.com/kiwimccomb-maker/ThreadMeisterExtended) (fork by Connor McComb). "Local files" below are files of that fork, not of ThreadMeister.

## Summary

- **Q1, Thomas Sanladerer's numbers.** The article and the video description give **no numbers** for the ridges, and they state no sizing rule. They link to **one Onshape model, for M3 only**. Its public part studio holds exact values: a Ø3.2 bore, three Ø1.5 ridge circles centred 2.05 from the hole axis, and a ridge inner circle of Ø2.6. That gives 0.3 of ridge protrusion. The ridges start flush at the top and reach full depth over a 1.5 lead-in, which is about 78.7° from the top face. The cutter body is 15 deep. No other sizes were published.
- **ThreadMeisterExtended's M3 row is Thomas's M3 model, number for number** (3.2 / 1.5 / 2.05 / 3 ridges). The default `grip_chamfer_angle = 78` also matches the angle of Thomas's lead-in. The other eight sizes (M1.6–M10) are not in any public source I could find. The Readme says they are untested ("they look about right to me").
- **Q2, other sources.** Only a few public sources give numbers, and none of them is a measured strength test of the ribbed hole:
  - a community Onshape FeatureScript (M3–M6 presets), whose inner diameters are much smaller than Thomas's;
  - Roland Smith's FreeCAD M3 crush-rib page (Ø3.1 bore, ribs down to Ø2.4);
  - a closed, unmerged FreeCAD pull request (bore = diameter + 0.15, rib protrusion 0.4, 3 ribs, 3 mm taper);
  - rahix's design guide, which describes the method but gives no thread-rib numbers.
  - I found no CNC Kitchen, Prusa or Bambu test or guide for ribbed screw holes.
- **Q3, what the ThreadMeisterExtended inner diameter tracks.** The inner diameter at the ridges (2 × (arc distance − ridge dia / 2)) **tracks the ISO pitch diameter D2**, within −0.13 to +0.02 for all nine shipped sizes. It sits **0.10–0.40 above the tap-drill size** (D − P), **0.13–0.52 above the internal minor diameter D1**, and **0.18–0.74 above the external minor diameter d3**. So the screw forms roughly 60–75 % of a full thread depth. Thomas's M3 (Ø2.6 against D2 = 2.675) follows the same pattern. My best guess is that the other sizes were scaled from M3, but nobody has stated a rule.
- **Inconsistency found.** The README table gives M6 an arc distance of **3.5**. `config.ini`, `core/tm_config.py` and `tests/test_config.py` all use **4.0**. With 3.5, the M6 ridge would protrude 1.0 and the inner diameter would be 4.3, below the tap drill and D1. That breaks the pattern of every other size, so 3.5 looks like a README typo.
- **Ridge chamfer.** Every shipped `grip_edge_chamfer` is 0.02–0.10 smaller than that size's ridge protrusion. This looks like a deliberate "chamfer away almost all of the ridge at the top" rule, which mirrors Thomas's lead-in. Again, nobody states this rule.

## Sources

Primary, owned by the person who made the claim:

1. Thomas Sanladerer, "A better way to add threads to your 3D prints", toms3d.org, 2025-01-14. https://toms3d.org/2025/01/14/a-better-way-to-add-threads-to-your-3d-prints/
2. Made with Layers (Thomas Sanladerer), YouTube video of the same name, published 2025-01-10, length 11:27, with its description. https://www.youtube.com/watch?v=HgEEtk85rAY
3. Thomas Sanladerer's Onshape document "M3 tapless" (owner "Toms3d.Org", created 2024-12-02, last modified 2025-03-10), Part Studio 1. https://cad.onshape.com/documents/ad7619552b9fa83ea94a898f/w/360bcf64e5c7dbaf68a34c94/e/ef194ff7bc5465936e1298fb . I read it through Onshape's anonymous public REST API (`/api/partstudios/d/…/w/…/e/…/features`), which returns the sketch dimensions and feature parameters.
4. joshua_wise822 (Accelerated Tech), "Custom feature: tapless (self-forming) screws", Onshape forum, April 2025. https://forum.onshape.com/discussion/27441/custom-feature-tapless-self-forming-screws . The feature's document is "Tapless Screw Feature", created 2025-04-07: https://cad.onshape.com/documents/3f129486c90c39e087c587e9/w/2e3f538eb10df254726a08d9/e/59f4cc80ed60d26042c424dd
5. Roland Smith, "Crush ribs for M3 screws in 3D prints", 2025-05-25. https://rsmith.home.xs4all.nl/3d-printing/crush-ribs-for-m3-screws-in-3d-prints.html
6. BootsSiR, FreeCAD PR #19149 "Added support for adding self forming threads to the hole tool", opened 2025-01-20, closed without merging. https://github.com/FreeCAD/FreeCAD/pull/19149
7. rahix, "Design for 3D printing", 2025-05-04, rule R5.4 "Rib Thread Forming" and rule R2.9 "Crush Ribs". https://blog.rahix.de/design-for-3d-printing/
8. Michael K Johnson, Mastodon post and thread, 2025-05-10. https://social.makerforums.info/@mcdanlj/114485353927845276
9. blue_haniwa, "Customizable 3D printer friendly standoff", Thingiverse. https://www.thingiverse.com/thing:6964224
10. MakerWorld (Bambu Lab account), "How to Design Screw Holes for 3D Printing?", 2025-12-18. https://forum.bambulab.com/t/how-to-design-screw-holes-for-3d-printing/217352

Thread standards (the standards themselves are paywalled, so I used a summary):

11. ISO metric screw thread (Wikipedia summary of ISO 68-1, 261, 262 and 724): formulas, coarse pitches and the tap-drill rule. https://en.wikipedia.org/wiki/ISO_metric_screw_thread
12. ISO 724:2023 preview page. It notes that the 2023 edition added the symbol d3 and changed the formula for the external minor diameter. https://webstore.ansi.org/preview-pages/ISO/preview_ISO+724-2023.pdf . I could not open the full text.

Local files read: `Readme.md`, `config.ini`, `core/tm_config.py` (`get_default_grip_ridge_inserts`), `core/tm_geometry.py` (`addAngleChamferToEdge`) and `tests/test_config.py`.

## Q1: Did Thomas publish concrete dimensions?

### Article [1]

There are no numbers for the bore, ridge, protrusion, depth or count, apart from "three", and there is no percentage rule. The relevant statements are these:

- The design "reduces the cross-section that the screw has to deform down to three individual ridges". It also says: "Because the overall hole is a little larger than the screw, these ridges can be designed to have a larger overlap with the screw threads". [1]
- On print orientation: "as long as you orient one ridge straight down, it's going to print just fine." [1]
- On scope: "What I'll personally be using for low- to medium-strength applications is the self-forming threads up to M5" (and printed threads beyond that). [1]
- On method: model the negative space once in Onshape, then derive it and boolean-subtract it at each hole. Thomas also mentions adding "the cutout geometry for the through-hole part, too" for M3x10 screws. [1]
- The article does contain the phrases "center bore size" and "standard clearance size", but they belong to the tapped-hole and slide-in-nut sections, not to the ridge design. [1]

### Video description [2]

There are no dimensions. The relevant link is "Onshape file for the M3 tapless threads" (source [3]). The chapter "Self-forming threads" runs from 05:09 to 07:19. I could not download the video transcript because YouTube refused the caption request, so **I have not checked whether a number is spoken in the video**. The article reads like the video script, but I have not confirmed that.

### Onshape model [3]: the only primary numbers

The document is called **"M3 tapless"**. It has one Part Studio, one Assembly and one BOM, with **M3 only**. The feature tree reads like this:

| Feature | What it does | Values |
|---|---|---|
| Sketch 1 | Three circles on the top plane | Ø3.2 bore circle (r 1.6). A concentric Ø2.6 circle (r 1.3). A Ø1.5 ridge circle, constrained tangent to the outside of the Ø3.2 circle, with its centre at 2.35 on the vertical axis. |
| Extrude 1 | New body (the negative space of the hole) | Ø3.2, **15** deep |
| Sketch 2 | Sweep path, drawn on a section through the axis | A line from radius 2.35 at the top to radius **2.05** at depth **1.5**, then a vertical line at radius 2.05 down to depth 15. A 1.5 length dimension sits on the taper. |
| Sweep 1 | Sweeps the Ø1.5 ridge circle along that path | — |
| Circular pattern 1 | **3** instances, operation REMOVE | The ridge bodies are cut out of the hole body, so they stay as plastic in the part. |
| Transform 1 | Copies the hole body 12 to the side | — |
| Sketch 3 / Extrude 2 | Added to the copy, on the opposite side | Ø**3.5**, 5 long (through-hole for the screw in the mating part) |
| Sketch 4 / Extrude 3 | Added to the copy | Ø**6**, 10 long (screw-head clearance) |

What this means for the finished hole:

- Bore Ø3.2.
- Ridge circles Ø1.5, with centres 2.05 from the axis. The inner edge of each ridge is at 2.05 − 0.75 = 1.30, so the **inner diameter is 2.6**. That matches the explicit Ø2.6 circle in Sketch 1, so 2.6 is clearly the design intent.
- **Protrusion** = 1.6 − 1.3 = **0.3**.
- **Lead-in**: at the top surface the ridge sits outside the bore (tangent, so zero protrusion). It moves inward to full protrusion 1.5 below the surface. That is a 0.3 radial × 1.5 axial taper, atan(1.5 / 0.3) = **78.7° from the top face**.
- **Count**: 3.
- **Depth**: the cutter is 15 long. This is a tool length, not a recommended engagement. In the M3x10 variant, a 5 long Ø3.5 section for the mating part sits above the ridges. My **guess** is that this means about 5 of thread engagement for an M3x10, but Thomas does not say so.

Caveat: the document was last modified on 2025-03-10, about two months after the article. The values above are from the current workspace. They may differ from what was shown in the video.

**No rule** (such as "inner diameter = minor diameter" or "x % of nominal") is stated anywhere by Thomas. The only person who comments on the missing numbers is Michael K Johnson: "Thomas Sanladerer didn't describe any dimensions for the ribs he used, just published a design in OnShape" [8]. (That post wrongly calls them "CNC Kitchen's self-forming threads".)

## Q2: Other design guides with numbers

| Source | Primary? | Numbers given | Test data? |
|---|---|---|---|
| Onshape "Tapless Screw Feature" by joshua_wise822 [4] | Yes. The author's own feature. The code snippet is quoted in a forum reply by martin_kopplow. | Presets as printed in the forum: **M3** inner 2.1, clearance 3.2, `insetKnobRadius` 3, lead-in 2. **M4** 3.0 / 4.2 / 5 / 2. **M5** 3.9 / 5.2 / 7 / 3. **M6** "4,2" (sic) / 6.2 / 8 / 3. The rib count is fixed at 3 (the base part studio has a circular pattern ×3). In the base part studio the knob circle is tangent to the outside of the clearance circle and is swept inward, the same construction as Thomas's model. Its current configuration shows clearance 3.2, inner Ø2.35, knob Ø5. The README says the defaults "seem to work well in FDM PETG and SLS Nylon". | No. Anecdotes only. martin_kopplow used 5 knobs for an M8x0.5 insert and suggests a knob offset "only say 10% more than the thread depth" as a starting point. |
| Roland Smith, M3 crush ribs [5] | Yes | M3: bore **Ø3.1**, **3** ribs bulging toward the "core diameter of the thread (⌀2.4 mm)". Rib bulge diameter "equal to inner diameter of M3 screws". The ribs do not start at the top of the hole. | Qualitative only: "a decent balance between friction and holding power". No Sanladerer credit. |
| FreeCAD PR #19149 [6] | Yes (code), never merged | `numberOfThreaders = 3`, `boreHoleMargin = 0.15` (bore = hole diameter + 0.15), `selfThreaderHeight = 0.4` (protrusion), `taperLength = 3.0`. The ribs are arcs of a cylinder 5 larger in radius than the bore, so they are almost flat chords, not small circles. For M3 with a 3.0 diameter this would give a bore of 3.15 and an inner diameter of about 2.35. | No. The author says they "tried this thread type and found it worked well". |
| rahix design guide [7] | Yes | R5.4 says to use rib thread forming for no-post-processing, low-reuse threads, and credits Thomas. It gives **no thread-rib numbers**. The only numbers are for press-fit crush ribs (R2.9): undersize the ribs by 0.2 and oversize the bore by 0.4. | No |
| Michael K Johnson + rahix thread [8] | Yes (opinion) | No numbers. They discuss using flat chords instead of semicircles for horizontal holes. rahix replies that semicircle ribs print fine horizontally "as long as you rotate them so one rib is on the bottom". | No |
| blue_haniwa Thingiverse standoff [9] | Yes | Uses the method and credits Thomas. The description has no dimensions, and I did not open the OpenSCAD file. | No |
| Bambu/MakerWorld screw-hole guide [10] | Guide, not a described test | Plain round holes only, no ribs. For example, M3 machine screw in PLA: 2.90 horizontal / 2.72 vertical. BT3 self-tapping screw in PLA: 3.00 / 2.55. | No method described |
| CNC Kitchen (Stefan Hermann) | — | I found **no** CNC Kitchen test of ribbed or self-forming holes. Their M3–M10 thread test covers modelled threads only. | — |
| Prusa knowledge base, Bambu wiki | — | I found nothing on ribbed screw holes. | — |

Not found: any public strength or pull-out test that compares rib sizes. I also could not read a Printables "metric self tap hole test" (PPat, model 1338667), because the page returned 403. Judging by its title, it covers plain holes from 1 to 5 mm.

## Q3: ThreadMeisterExtended table compared with ISO and with Thomas

Reference values for metric coarse threads, using D = nominal diameter and P = pitch (coarse pitches from ISO 262 via [11]):

- **D1** (internal minor diameter) = D − 1.082532·P [11]
- **d3** (external root diameter) = D − 1.226869·P. This is the classic ISO 724:1993 / ISO 898-1 formula. It is **not verified against ISO 724:2023**, which changed this formula [12].
- **D2** (pitch diameter) = D − 0.649519·P [11]
- **Tap drill** ≈ D − P [11]

ThreadMeisterExtended values are taken from `config.ini` and `core/tm_config.py`. The calculated columns are:

- **inner r** = arc − ridge/2
- **eff ID** = 2 × inner r (the inner diameter at the ridges)
- **protr** = clearance/2 − inner r (how far each ridge sticks into the bore)

| Size | P | Clear. | Ridge Ø | Arc | N | inner r | **eff ID** | **protr** | D1 | d3 | tap D−P | D2 | eff−D1 | eff−d3 | eff−tap | **eff−D2** | eff/D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1.6 | 0.35 | 1.8 | 0.8 | 1.075 | 3 | 1.075−0.40=0.675 | 1.350 | 0.900−0.675=0.225 | 1.221 | 1.171 | 1.25 | 1.373 | +0.129 | +0.179 | +0.100 | −0.023 | 0.844 |
| M2 | 0.4 | 2.2 | 1.0 | 1.35 | 3 | 1.35−0.50=0.850 | 1.700 | 1.10−0.85=0.250 | 1.567 | 1.509 | 1.60 | 1.740 | +0.133 | +0.191 | +0.100 | −0.040 | 0.850 |
| M2.5 | 0.45 | 2.7 | 1.25 | 1.725 | 3 | 1.725−0.625=1.100 | 2.200 | 1.35−1.10=0.250 | 2.013 | 1.948 | 2.05 | 2.208 | +0.187 | +0.252 | +0.150 | −0.008 | 0.880 |
| **M3** | 0.5 | 3.2 | 1.5 | 2.05 | 3 | 2.05−0.75=1.300 | **2.600** | 1.60−1.30=**0.300** | 2.459 | 2.387 | 2.50 | 2.675 | +0.141 | +0.213 | +0.100 | −0.075 | 0.867 |
| M4 | 0.7 | 4.2 | 2.0 | 2.75 | 3 | 2.75−1.00=1.750 | 3.500 | 2.10−1.75=0.350 | 3.242 | 3.141 | 3.30 | 3.545 | +0.258 | +0.359 | +0.200 | −0.045 | 0.875 |
| M5 | 0.8 | 5.3 | 2.5 | 3.5 | 4 | 3.5−1.25=2.250 | 4.500 | 2.65−2.25=0.400 | 4.134 | 4.019 | 4.20 | 4.480 | +0.366 | +0.481 | +0.300 | +0.020 | 0.900 |
| M6 (config 4.0) | 1.0 | 6.3 | 2.7 | 4.0 | 5 | 4.0−1.35=2.650 | 5.300 | 3.15−2.65=0.500 | 4.917 | 4.773 | 5.00 | 5.350 | +0.383 | +0.527 | +0.300 | −0.050 | 0.883 |
| *M6 (README 3.5)* | 1.0 | 6.3 | 2.7 | *3.5* | 5 | 3.5−1.35=2.150 | *4.300* | 3.15−2.15=*1.000* | 4.917 | 4.773 | 5.00 | 5.350 | −0.617 | −0.473 | −0.700 | −1.050 | 0.717 |
| M8 | 1.25 | 8.3 | 3.5 | 5.3 | 5 | 5.3−1.75=3.550 | 7.100 | 4.15−3.55=0.600 | 6.647 | 6.466 | 6.75 | 7.188 | +0.453 | +0.634 | +0.350 | −0.088 | 0.887 |
| M10 | 1.5 | 10.3 | 4.0 | 6.45 | 6 | 6.45−2.00=4.450 | 8.900 | 5.15−4.45=0.700 | 8.376 | 8.160 | 8.50 | 9.026 | +0.524 | +0.740 | +0.400 | −0.126 | 0.890 |
| Thomas M3 [3] | 0.5 | 3.2 | 1.5 | 2.05 | 3 | 1.300 | 2.600 | 0.300 | 2.459 | 2.387 | 2.50 | 2.675 | +0.141 | +0.213 | +0.100 | −0.075 | 0.867 |

For comparison, the other sources' M3 inner diameters are: FeatureScript preset 2.1 [4], Roland Smith 2.4 [5], FreeCAD PR about 2.35 [6], and ThreadMeisterExtended and Thomas 2.6.

What the numbers show:

1. **The effective inner diameter does not track the minor diameter or the tap drill.** It is always larger than both, by an amount that grows with size (eff − tap: 0.10, 0.10, 0.15, 0.10, 0.20, 0.30, 0.30, 0.35, 0.40).
2. **It tracks the pitch diameter D2 closely**: within −0.126 to +0.020 for every shipped size. In other words, the ridges reach in about to the thread's pitch line. The screw forms about (D − eff)/(D − D1) = 58–74 % of the basic thread depth. This is consistent with Thomas's remark about "a larger overlap with the screw threads" in an oversized bore. Thomas never names D2, though.
3. **Clearance** is D + 0.2 for M1.6–M4 and D + 0.3 for M5–M10. M3 = 3.2 is Thomas's value.
4. **Ridge diameter** is exactly D/2 for M1.6–M4 (0.8, 1.0, 1.25, 1.5, 2.0). It is 2.5 for M5 (= D/2), then 2.7, 3.5 and 4.0 for M6, M8 and M10. M3 = 1.5 = D/2 is Thomas's value. The M6–M10 ridge sizes and counts (5, 5, 6) have no public source.
5. **Count**: 3 for M1.6–M4 (as Thomas), then 4, 5, 5 and 6. Neither Thomas nor [4] or [5] uses more than 3 ribs for these sizes. The only mention of 5 knobs is martin_kopplow's M8x0.5 anecdote in [4].
6. **Fit checks** (calculated): every ridge circle crosses the bore wall. Neighbouring ridge circles never overlap: the distance between ridge centres, 2·arc·sin(180°/N), is always greater than the ridge diameter. At the bore wall, each ridge covers 30°–42° of arc out of the 60°–120° spacing.
7. **Chamfer and lead-in.** Thomas's model uses a swept taper, 0.3 radial over 1.5 deep (78.7°). ThreadMeisterExtended instead chamfers the top edge of each ridge arc. It uses Fusion's distance-and-angle chamfer with the angle measured from the face plane (`core/tm_geometry.py`, `addAngleChamferToEdge`), and the default angle is 78°. That matches Thomas's taper. The chamfer distances are each 0.02–0.10 smaller than the protrusion (for example M3: 0.28 against 0.30). If the distance is measured along the top face, the lead-in depth is chamfer × tan 78° ≈ 4.70 × chamfer: about 0.94 (M1.6), 1.32 (M3), 1.98 (M6) and 2.82 (M10). Which face Fusion measures the distance on depends on the edge, so I have not verified that this is what the model actually gets.
8. **Depth** (4, 5, 6, 7, 8, 9, 10, 12, 14) is about D + 2 to D + 4. Thomas's cutter is 15 long for M3 and gives no engagement advice. I found no public source for these depths.

## Open questions for Connor McComb (the fork author)

1. Was M3 copied from Thomas's Onshape "M3 tapless" model (Ø3.2 / Ø1.5 ridges at 2.05 / ×3)? The numbers match exactly.
2. How were the other sizes derived? Was the rule "inner diameter ≈ pitch diameter", "ridge = D/2", "clearance = D + 0.2/0.3", or something else? Did any of them come from a source, or by eye? (The README says they are untested.)
3. Is the M6 arc distance 3.5 (README) or 4.0 (config, code, tests)? 3.5 would give a 1.0 protrusion and a 4.3 inner diameter, which looks wrong.
4. Why move from 3 ridges to 4, 5, 5 and 6 above M4? Was it to keep the ridge width small, or for print orientation? Thomas says to orient "one ridge straight down" for horizontal holes, which is easy with 3 ridges and different with 4–6.
5. Where do the depths come from (D + 2 to D + 4)? Is a depth meant as the thread engagement length?
6. Is `grip_edge_chamfer` meant to be "protrusion minus a little", and is the 78° angle taken from Thomas's 0.3 × 1.5 taper? Which face does the Fusion chamfer distance run along?
7. Has anyone printed the M1.6, M2 and M2.5 sizes? Their ridges are 0.8–1.25 in diameter with 0.225–0.25 of protrusion, which is close to a 0.4 nozzle's line width.
8. Small fix: the README spells the name "Salanderer". It is **Sanladerer**.

## Not found / not verified

- No numbers from Thomas for any size other than M3. No sizing rule from Thomas.
- I could not get the video transcript, so I have not checked whether a number is spoken in the video.
- No CNC Kitchen, Prusa knowledge base or Bambu wiki material on ribbed self-forming holes.
- No measured strength comparison of rib sizes from any source.
- I did not verify the d3 formula against ISO 724:2023.
- I could not read the source code of the Onshape FeatureScript: the API needs a login for feature studios. Its preset numbers come from the forum reply quoting it [4].
