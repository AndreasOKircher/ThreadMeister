# Development Notes

## Platform Support

### Windows
- Fully tested and verified.
- All UI elements, icons, and geometry operations behave as expected.

### macOS
- Not yet tested due to lack of local hardware.
- Code uses `os.path.join` for cross-platform path handling.
- No Windows-specific APIs or assumptions are used.
- Fusion 360's Python environment is consistent across platforms, so compatibility is expected.
- Icon loading should work identically as long as the folder structure is preserved.
- Future task: verify installation, icon rendering, and geometry creation on macOS.

## Project File Structure

```
ThreadMeister/
├── ThreadMeister.py          ← Entry point: run(), stop(), imports
├── ThreadMeister.manifest    ← Fusion 360 runtime manifest
├── manifest.json             ← Autodesk App Store manifest
├── config.ini                ← User-editable insert specs and settings
├── ThreadMeister.png         ← Add-in icon (App Store)
├── License.txt               ← MIT License
├── Readme.md                 ← GitHub README
├── Readme_AppStore.md        ← Autodesk App Store README
├── core/
│   ├── tm_state.py           ← Global state: INSERT_SPECS, CONFIG, tolerances
│   ├── tm_config.py          ← Config I/O: load/save config.ini
│   ├── tm_helpers.py         ← Utility: point/circle comparison, calc_blind_hole_depth
│   ├── tm_geometry.py        ← Geometry: profile selection, extrude direction, chamfer, fillet
│   ├── tm_execute.py         ← Execution: CommandExecuteHandler (hole creation loop)
│   ├── tm_ui.py              ← UI: CommandCreatedHandler, input handlers
│   └── tm_debug_export.py    ← Debug: export sketch data to JSON fixtures
├── resources/
│   ├── icons/                ← Toolbar icons (16x16 – 128x128)
│   └── images/               ← Screenshots, title graphic, animated GIF
├── scripts/
│   ├── deploy.bat            ← Copy add-in to Fusion 360 scripts folder
│   ├── visualize_profiles.py ← Matplotlib visualization of exported fixtures
│   └── profile_inspector.py  ← Interactive profile/curve inspector
├── fixtures/                 ← JSON test fixtures exported from Fusion 360
├── tests/
│   ├── conftest.py           ← Pytest config: adsk mock, path setup
│   ├── test_helpers.py       ← Tests for tm_helpers
│   ├── test_config.py        ← Tests for tm_config
│   ├── test_geometry.py      ← Tests for tm_geometry filter functions
│   └── test_profile_selection.py ← Fixture-based profile selection tests
├── fixture_inspector.py      ← Standalone fixture JSON viewer
└── docs/
    ├── development-notes.md  ← This file
    └── changelog.md          ← Version history
```

## Code Structure (v1.2.0 — modular)

### Module responsibilities

| Module | Description |
|--------|-------------|
| `tm_state.py` | Global state: `INSERT_SPECS` dict, `CONFIG` dict, tolerances, UI reference |
| `tm_config.py` | Config file I/O: load/save `config.ini`, default insert specs |
| `tm_helpers.py` | Utilities: `isSamePoint()`, `isSameCircle()`, `calc_blind_hole_depth()`, `log()` |
| `tm_geometry.py` | Core geometry: `findProfileForCircle()`, `findExtrudeDirectionFromSketch()`, `findChamferEdge()`, `addChamferToEdge()`, `findDistanceThroughBody()`, `addBottomRadiusToBlindHole()` |
| `tm_execute.py` | `CommandExecuteHandler.notify()` — orchestrates the hole creation loop |
| `tm_ui.py` | `CommandCreatedHandler`, `InputChangedHandler`, `ValidateInputsHandler` |
| `tm_debug_export.py` | JSON export of sketch profiles/curves for debugging and test fixtures |

### Execution flow (v1.2.0)
```
User clicks ThreadMeister button
  → CommandCreatedHandler: build UI dialog
  → User selects body, points, options, clicks OK
  → CommandExecuteHandler: for each selected point:
      ├─ Create clean temp sketch via addWithoutEdges(face)
      ├─ Project original sketch point into temp sketch
      ├─ Draw bore circle, constrain to projected point
      ├─ findProfileForCircle(tempSketch, circle) → select profile
      ├─ findExtrudeDirectionFromSketch(parentSketch) → determine cut direction
      ├─ Extrude cut (blind or through)
      ├─ Optional: findChamferEdge() + addChamferToEdge()
      └─ Optional: addBottomRadiusToBlindHole()
  → Group all timeline entries under one group
  → Show result message
```

### Profile selection algorithm (`findProfileForCircle`)

Four-stage filter chain in `tm_geometry.py`:

1. **Area filter** — reject profiles with area > 1.01 × target circle area
2. **Centroid filter** — reject profiles whose centroid is farther than `radius` from circle center
3. **Curve-point filter** — reject profiles containing curves that don't touch the circle (skips `isReference` curves)
4. **Accumulation** — combinatorial search for the subset of remaining profiles whose combined area equals the target circle area

With the clean temp sketch approach (v1.2.0), the sketch contains only the bore circle, so there are exactly 2 profiles and the algorithm trivially picks the smaller one.

## Phase 5 — Clean Temp Sketch Approach (v1.2.0)

### The problem: projected 3D geometry

When a sketch is created on a face of a solid body, Fusion 360 automatically projects the body's edges onto the sketch plane as reference curves. These projected curves:

- Are invisible to the user in normal sketch editing
- Subdivide sketch profiles unpredictably
- Create phantom profile boundaries that vary with body geometry
- Make `findProfileForCircle()` unreliable — the bore circle's profile gets split by projected edges crossing the bore area

Previously, ThreadMeister added the bore circle directly to the user's existing sketch. This worked for simple cases but failed when projected body edges intersected the bore area.

### The solution: `addWithoutEdges(face)`

Instead of drawing in the user's sketch, ThreadMeister now creates a temporary clean sketch per bore:

```python
face = parentSketch.referencePlane
tempSketch = component.sketches.addWithoutEdges(face)  # no body edge projections
projectedPoint = tempSketch.project(point).item(0)      # parametric link
circle = tempSketch.sketchCurves.sketchCircles.addByCenterRadius(
    projectedPoint.geometry, radius)
```

Key properties:
- **`addWithoutEdges(face)`** creates a sketch on the same face but without auto-projected body edges. The sketch is completely empty.
- **`tempSketch.project(point)`** projects the user's original sketch point into the temp sketch, maintaining a parametric association. If the user moves the original point, the bore follows.
- The temp sketch contains only: 1 projected point + 1 bore circle = exactly 2 profiles. Profile selection is trivial.
- Temp sketches are named `TM_{insertName}_P{n}` (e.g., `TM_M3_P1`).
- All temp sketches are captured in the timeline group alongside the extrude/chamfer/fillet features.

### Failure handling

- If `findProfileForCircle()` returns `None`: the temp sketch is deleted via `tempSketch.deleteMe()`, the point is skipped, and the failure count is incremented.
- If `findExtrudeDirectionFromSketch()` returns `None`: same — temp sketch deleted, point skipped.
- The user's original sketch is never modified.

### What this replaces

The old approach (v1.1.x):
```python
# OLD: drew bore circle in user's sketch (contaminated by projections)
circle = parentSketch.sketchCurves.sketchCircles.addByCenterRadius(center2d, radius)
constraints.addCoincident(circle.centerSketchPoint, point)
profile = findProfileForCircle(parentSketch, circle)  # could fail due to projections
```

### Future optimization: shared temp sketch

When multiple points are selected from the same parent sketch, it's possible to create only 1 temp sketch per source sketch instead of 1 per point. This would reduce feature tree clutter. Not yet implemented — see memory for details.

### Graph reconstruction (documented, not implemented)

An alternative approach was considered: build a 2D endpoint graph from sketch curves (excluding `isReference` and `isConstruction`), merge collinear segments split by projections, walk closed loops to find the bore profile, and map back to Fusion profiles. This is significantly more complex and was not needed once the clean temp sketch approach proved sufficient. If `addWithoutEdges` ever becomes unavailable or insufficient, this remains a viable fallback strategy.

## Known Technical Limitations

### Through-hole extrusion stability
Fusion 360 may fail to create through-hole extrusions in certain situations:

Symptoms include:
- Missing through-hole cut.
- Partial cut that stops before exiting the body.

Workarounds:
- Ensure the target body has clean, manifold geometry.

### Profile recognition (largely resolved in v1.2.0)
The clean temp sketch approach eliminates most profile recognition issues caused by projected geometry. Remaining edge cases:

- Bodies with complex topology or thin walls where Fusion struggles to resolve the cut.
- Cases where the extrusion direction is ambiguous.

The old workarounds (simplify sketch, use construction geometry, move bore point to separate sketch) are no longer necessary — ThreadMeister now creates its own clean sketch automatically.

### Bounding Box Filter Infeasibility
**Finding (Phase 4, 2026-03-12):** Attempted to use profile bounding boxes as a coarse filter to speed up profile selection.

**Issue:** Fusion 360's `profile.boundingBox` calculations are too imprecise for reliable geometric filtering:
- Tested with 100% margin expansion (center +/- 2.0x radius): Too permissive, let through all profiles
- Tested with 10% margin expansion (center +/- 1.1x radius): Still unreliable — rejected valid profiles incorrectly

**Root cause:** The API's bounding box calculations don't match expected geometric relationships. Impossible to calibrate a margin that works reliably across all sketch geometries.

**Decision:** Removed BBox filter entirely. The four-stage filter chain (area, centroid, curve-points, accumulation) is reliable. With the clean temp sketch approach, the filter chain is rarely exercised since there are only 2 trivial profiles.
