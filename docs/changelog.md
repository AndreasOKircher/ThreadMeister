# Changelog

## 1.1.0b — 2026-03-10 — Code organization & sub-function refactoring
- **Modules moved to `core/` subdirectory** for cleaner project structure
- **Updated deploy script** to copy modules from `core/` subdirectory
- **Refactored `findProfileForCircle()`** into testable sub-functions:
  - `_filter_by_area()` – coarse area validation
  - `_filter_by_centroid()` – coarse centroid distance check
  - `_filter_by_bounding_box()` – coarse bounding box containment
  - `_accumulate_profiles()` – precise profile area matching
- **Improved code testability** – each filter function can be tested independently
- **Foundation for Phase 2** – prepares for pytest unit tests and Phase 3 fixture-based testing
- No functional changes – all features work identically to v1.1.0
- ✅ Verified working in Fusion 360 (blind holes, through holes, chamfer, fillet)

## 1.1.0 — 2026-03-09 — Refactoring into modules
- Split monolithic `ThreadMeister.py` (~1500 lines) into 6 focused modules:
  - `tm_state.py` – shared globals, constants
  - `tm_config.py` – config loading, validation, saving
  - `tm_helpers.py` – geometry comparisons, logging, `calc_blind_hole_depth()`
  - `tm_geometry.py` – profile finding, extrusion, chamfer, fillet
  - `tm_execute.py` – `CommandExecuteHandler` (main hole creation loop)
  - `tm_ui.py` – UI event handlers, info text
- `ThreadMeister.py` is now a thin entry point (`run()` / `stop()` only)
- Removed dead code (duplicate import/config block from lines 1221-1249)
- No functional changes – identical behaviour to v1.0.1

## 1.0.1 — 2026-03-07 — Documentation update
- Switched license from GPL-3.0 to MIT
- Added animated GIF demo to README and App Store README
- Added "Why ThreadMeister?" section to both READMEs
- Added ScreenToGif credit
- README layout improvements (centered headline, image spacing)
- Cleaned up duplicate icon files from resources/ root

## 1.0.0 — 2026-02 — Initial Release
- First public release of ThreadMeister.
- Distributed simultaneously on **GitHub** and the **Autodesk App Store** (release pending).
- Tested on Windows; macOS support expected but not tested
- Known limitation: through‑hole extrusions may fail in certain sketch or geometry configurations
- Added support for all CNC Kitchen insert sizes (M2–M10, 1/4"-20).
- Added blind and through hole options.
- Added automatic chamfer and optional bottom fillet.
- Added multi-point hole creation.
- Added timeline grouping for clean parametric workflows.
- Added SOLID → MODIFY menu integration.
- Added documentation and packaging for the Autodesk App Store.



