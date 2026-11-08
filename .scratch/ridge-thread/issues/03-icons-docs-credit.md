# Bore Type icons, user docs and credits

Status: completed

## Parent

`.scratch/ridge-thread/PRD.md`

## What to build

1. **Icons:** copy `../ThreadMeisterExtended/resources/icons/heatset/` and
   `../ThreadMeisterExtended/resources/icons/gripridge/` (16/32/64/128 px) into
   `resources/icons/heatset/` and `resources/icons/ridgethread/`. Show them in the Bore Type
   dropdown with `LabeledIconDropDownStyle`, as the fork does (`_addInsertTypeInput` in the
   fork's `core/tm_ui.py`). Check that `scripts/package.bat` includes the new folders.
2. **Docs:** `Readme.md` and `resources/help.html`: Ridge Thread section (what it is, sizes,
   `[Ridge Threads]` config, print tip "orient one ridge straight down", recommended up to M5).
   `docs/changelog.md` entry.
3. **Credits** (required by the MIT license for the copied icons and chamfer code; user wants
   them visible):
   - `Readme.md` credits section: concept by Thomas Sanladerer (link to his article, courtesy
     credit); first Fusion implementation by Connor McComb (ThreadMeisterExtended, link).
   - `Readme.md` and `License.txt`: "Icons and Ridge Thread chamfer code adapted from
     ThreadMeisterExtended, © 2026 Connor McComb, MIT license."

Own icon design: separate later issue, not this one. The icons are temporary. When they are
replaced, drop "Icons and" from the credit line; the chamfer-code credit stays.

## Acceptance criteria

- [x] ~~Bore Type dropdown icons~~ dropped by user decision.
- [x] ~~Icon folders in zip~~ dropped (no icons). `package.bat` already copies `tm_ridge.py`.
- [x] Readme, help.html and changelog describe Ridge Thread; credits present.
- [x] `python -m pytest -q` passes.

## Blocked by

`.scratch/ridge-thread/issues/01-ridge-thread-bore.md`

## Implementation Summary

User decision (2026-11-08): NO Bore Type icons (no icon idea for Ridge Thread yet), so no icons were copied and no dropdown change was made. Docs: `Readme.md` (Ridge Thread section, v1.3.0 changelog, credits, new header picture `resources/images/Title_RidgeThread_v6.png`), `resources/help.html` (Ridge Thread + Credits), `License.txt` (chamfer-code credit; the "Icons and" part is dropped because no icons were copied). `docs/changelog.md` was already updated in issues 01-02. Tests pass. Docs-only issue, no Fusion smoke test needed.
