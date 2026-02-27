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

## Code Structure
ThreadMeister is implemented as a standard Fusion 360 Python add-in. The main components are:

- **ThreadMeister.py** — main entry point, command creation, UI logic, geometry generation.
- **manifest.json** — metadata for Fusion 360 and the Autodesk App Store.
- **config.ini** — insert specification definitions and configurable parameters.
- **resources/icons/** — toolbar icons in multiple resolutions.
- **resources/images/** — screenshots and title graphics for documentation.

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

