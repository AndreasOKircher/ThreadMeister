# Bore Type icons, user docs and credits

Status: ready-for-agent

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
3. **Credits** in `Readme.md`: concept by Thomas Sanladerer (link to his article); first Fusion
   implementation and the icons by Connor McComb (ThreadMeisterExtended, MIT,
   © 2026 Connor McComb). Keep his copyright notice for the copied icons.

Own icon design: separate later issue, not this one.

## Acceptance criteria

- [ ] Manual Fusion smoke: Bore Type dropdown shows an icon next to each item.
- [ ] Packaged zip (`scripts\package.bat`) contains the icon folders.
- [ ] Readme, help.html and changelog describe Ridge Thread; credits present.
- [ ] `python -m pytest -q` passes.

## Blocked by

`.scratch/ridge-thread/issues/01-ridge-thread-bore.md`

## Implementation Summary

<Filled at issue close.>
