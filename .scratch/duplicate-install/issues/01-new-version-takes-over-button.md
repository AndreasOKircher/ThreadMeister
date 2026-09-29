# Newer ThreadMeister takes over the button and reports other installations

Status: ready-for-human
GitHub: https://github.com/AndreasOKircher/ThreadMeister/issues/1

> **Status note.** Code done and unit-tested; waiting for the manual Fusion smoke test below.

## Parent

`.scratch/duplicate-install/idea.md`

## What to build

- `ThreadMeister.py` `run()`: if `commandDefinitions.itemById(CMD_ID)` already exists,
  delete its toolbar control and the definition, then create our own.
- New `core/tm_install.py`: `get_install_search_dirs()` (App Store `ApplicationPlugins`
  and manual `API\AddIns`, Windows and macOS) and `find_other_installs(own_dir, dirs)`
  (folders named `ThreadMeister*`, excluding the one containing this copy).
- `run()` shows `duplicate_install_message()` if other installs are found.
- `scripts/deploy.bat` and `scripts/package.bat` copy the new module.

### Behaviour by load order (versions before 1.2.4 can't be changed)

| Order | Result |
|---|---|
| old copy first, 1.2.4 second | 1.2.4 takes over the button; message shown |
| 1.2.4 first, old copy second | old copy fails with "already exists" (its own dialog); 1.2.4 keeps the button; message shown |

Known edge: stopping the old copy later runs its `stop()`, which deletes the button by ID
(ours by then). A Fusion restart restores it.

## Acceptance criteria

- [x] Unit tests for the folder search (own install excluded, bundle ↔ manual both ways,
      unrelated add-ins and files ignored, prefix edge case). 12 tests.
- [x] `python -m pytest -q` passes.
- [x] Changelog, README (changelog + Troubleshooting) updated; version 1.2.4.
- [ ] Manual Fusion smoke: with the old App Store copy **and** 1.2.4 both enabled at startup,
      restart Fusion → message lists the other copy; face-sketch Bore works (1.2.4 code runs).
- [ ] Only 1.2.4 installed → no message, button works.

## Blocked by

None.

## Implementation Summary

**Code done:** 2026-09-29, branch `duplicate-install-r1`

- 1.2.4 takes over `ThreadMeisterCmd` if another copy registered it first, and lists other
  ThreadMeister folders found in Fusion's add-in locations at startup.
- Tests: 12 new in `tests/test_install.py`; suite 76 passed, 12 skipped.
- `run()` itself can't be unit-tested (Fusion API) — covered by the smoke test.
- Manual Fusion smoke: **pending**.
