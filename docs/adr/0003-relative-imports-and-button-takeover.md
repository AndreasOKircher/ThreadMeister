# ADR-0003: Relative imports and button takeover for side-by-side installs

Status: accepted (2026-09-29) — implementation: `.scratch/duplicate-install/`

## Context

Users can have two ThreadMeister copies installed (App Store bundle under
`ApplicationPlugins`, manual install under `API\AddIns`). Up to 1.2.3:

- Both copies registered the command ID `ThreadMeisterCmd`; the second one to load crashed
  with "a command definition with that id already exists" and the first one kept the button.
- `ThreadMeister.py` added `core/` to `sys.path` and imported `tm_state`, `tm_execute`, … by
  bare name. Fusion runs all add-ins in one Python interpreter, so these names were shared:
  whichever copy loaded first supplied the code for both.

Checked in Fusion (2026-09-29, Text Commands): the entry file is registered under a name
derived from its install path (`__main__C%3A%2F…%2FAddIns%2FThreadMeister%2FThreadMeister_py`),
while the `tm_*` modules sat in `sys.modules` under their bare names.

Autodesk's guidance: use relative imports, don't modify `sys.path` (shared environment), and
delete an existing command definition before `addButtonDefinition` (Fusion API docs and
add-in template).

## Decision

1. All imports between our modules are relative (`from .core import tm_state`,
   `from . import tm_state`). Nothing is added to `sys.path`. Each copy's modules then live
   under its own path-derived package name.
2. `run()` deletes an existing `ThreadMeisterCmd` definition and toolbar control before
   creating its own.
3. No custom detection of other installs — a README troubleshooting entry instead.

## Consequences

- 1.2.4+ always runs its own code and owns the button when it loads second. If an older
  copy (≤1.2.3) loads after it, that copy shows its own "already exists" error; 1.2.4 keeps
  working. Stopping an older copy later deletes the button by ID (restart Fusion).
- Tests put the repo root on `sys.path` and import `core.tm_*` (a real package).
- Assumes Fusion loads the entry file as a package (required by Autodesk's template too);
  confirmed by the manual smoke test.

## Alternatives rejected

- **Purge cached `tm_*` modules from `sys.modules`** — works around the symptom, still
  modifies shared state, not what Autodesk recommends.
- **Scan install folders and warn the user** — no common practice, depends on install
  paths, needs "shown once" state in `config.ini`.
