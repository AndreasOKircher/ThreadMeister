# Changelog

## 1.2.0 — 2026-03-14 — Clean temp sketch approach
- **Major redesign of bore creation**: replaced drawing bore circle in user's sketch with creating a clean temporary sketch via `addWithoutEdges(face)`
- **Problem solved**: Fusion 360 auto-projects 3D body edges onto sketch planes as reference curves, which split bore profiles unpredictably and caused extrusion failures
- **New flow**: create projection-free temp sketch → project original point (parametric link) → draw bore circle → trivial 2-profile selection
- Temp sketches named `TM_{insert}_P{n}`, included in timeline group
- On failure, temp sketch is deleted and point is skipped — user's original sketch is never modified
- Added `isReference` curve skip in `_filter_by_curve_points`
- Added `is_reference` field to debug export curve data
- Removed all `log()` calls from `tm_geometry.py` and `tm_execute.py`
- Removed `diagnose_blind_hole()` diagnostic function
- Deleted scratch scripts (`analyze_loop3.py`, `test_curves_debug.py`, `test_import.py`)
- Updated `development-notes.md` with Phase 5 documentation
- ✅ All tests passing, verified in Fusion 360

## 1.1.2 — 2026-03-13 — Export & visualization infrastructure
- Added `tm_debug_export.py` for JSON export of sketch profiles/curves from Fusion 360
- Added `visualize_profiles.py` standalone matplotlib visualization tool
- Added `profile_inspector.py` interactive profile/curve inspector
- Added `test_profile_selection.py` fixture-based tests
- Added curve-point filter (`_filter_by_curve_points`) to `findProfileForCircle`
- Standardized logging with `[TM][filter_name]` prefix format
- Added debug export UI: `exportDebug` checkbox in dialog (behind `enable_debug_export` config flag)
- Export produces dual output: Fusion console `[EXPORT]` messages + JSON files to `debug_exports/`

## 1.1.1 — 2026-03-11 — Pytest test suite
- Added 49 comprehensive unit tests covering `tm_helpers`, `tm_config`, and `tm_geometry` filter functions
- Mock-based testing with zero Fusion 360 dependency
- `conftest.py` handles `adsk` module stubbing before imports
- Added test infrastructure: `pytest.ini`, `requirements-dev.txt`, `.venv` setup
- All tests pass and ready for CI/CD integration

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



