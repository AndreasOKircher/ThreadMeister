# Development Notes

## Platform Support

### Windows
- Fully tested and verified.
- All UI elements, icons, and geometry operations behave as expected.

### macOS
- Not yet tested due to lack of local hardware.
- Code uses `os.path.join` for cross‑platform path handling.
- No Windows‑specific APIs or assumptions are used.
- Fusion 360’s Python environment is consistent across platforms, so compatibility is expected.
- Icon loading should work identically as long as the folder structure is preserved.
- Future task: verify installation, icon rendering, and geometry creation on macOS.

## Project File Structure

```
ThreadMeister/
├── ThreadMeister.py          ← Main add-in (entry point, UI, geometry, config)
├── ThreadMeister.manifest    ← Fusion 360 runtime manifest
├── manifest.json             ← Autodesk App Store manifest
├── config.ini                ← User-editable insert specs and settings
├── ThreadMeister.png         ← Add-in icon (App Store)
├── License.txt               ← MIT License
├── Readme.md                 ← GitHub README
├── Readme_AppStore.md        ← Autodesk App Store README
├── resources/
│   ├── icons/                ← Toolbar icons (16x16 – 128x128)
│   └── images/               ← Screenshots, title graphic, animated GIF
└── docs/
    ├── development-notes.md  ← This file
    └── changelog.md          ← Version history
```

## Code Structure (v1.0.1 — monolithic)

ThreadMeister is implemented as a standard Fusion 360 Python add-in. Currently all logic is in a single file:

**ThreadMeister.py** (~1500 lines) contains:

| Section | Lines | Description |
|---------|-------|-------------|
| Config management | 61-352 | `load_config()`, `save_*()`, `get_default_inserts()`, `create_default_config()` |
| Entry point | 366-405 | `run()` — registers button in SOLID > MODIFY |
| UI handlers | 408-525 | `CommandCreatedHandler`, `InputChangedHandler`, `ValidateInputsHandler` |
| Profile selection | 529-657 | `findProfileForCircle()` — finds sketch profiles for bore extrusion |
| Main execution | 659-811 | `CommandExecuteHandler` — orchestrates hole creation loop |
| Geometry functions | 892-1463 | Extrude direction, chamfer edge, fillet, through-body distance |
| Helpers | 842-889 | Point/circle comparison, logging |
| Cleanup | 1506-1521 | `stop()` — unloads add-in |

**Note:** Lines 1221-1249 contain a duplicate import/config block (dead code) to be cleaned up in v1.1.0.

### Execution flow
```
User clicks ThreadMeister button
  → CommandCreatedHandler: build UI dialog
  → User selects body, points, options, clicks OK
  → CommandExecuteHandler: for each point:
      ├─ Create temporary bore circle at sketch point
      ├─ findProfileForCircle() → select profiles
      ├─ findExtrudeDirectionFromSketch() → determine cut direction
      ├─ Extrude cut (blind or through)
      ├─ Optional: findChamferEdge() + addChamferToEdge()
      └─ Optional: addBottomRadiusToBlindHole()
  → Group timeline entries
  → Show result message
```

### Planned refactoring (v1.1.0)
See `idea/refactoring-plan.md` for the module split plan into `tm_state`, `tm_config`, `tm_helpers`, `tm_geometry`, `tm_execute`, `tm_ui`.

The add-in registers a command under **SOLID → MODIFY**, using Fusion’s command definition API. Geometry creation is fully parametric and grouped in the timeline.
## Known Technical Limitations

### Through-hole extrusion stability
Fusion 360 may fail to create through-hole extrusions in certain situations:

Symptoms include:
- Missing through-hole cut.
- Partial cut that stops before exiting the body.

Workarounds:
- Ensure the target body has clean, manifold geometry.
  
### Profile recognition
- Sketches with many intersecting or overlapping profiles near the bore center.
- Imported DXF sketches with excessive or non‑manifold geometry.
- Bodies with complex topology or thin walls where Fusion struggles to resolve the cut.
- Cases where the extrusion direction is ambiguous or Fusion selects the wrong profile.

Symptoms include:
- Uncomplete extrusion of cyinder body (extrusion not based on complete circle).

Workarounds:
- Simplify the sketch around the bore location.
- Convert unnecessary lines to construction geometry.
- Move the bore point into a separate sketch.

