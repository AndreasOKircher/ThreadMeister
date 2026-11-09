# Live preview of the Bores before OK

Status: ready-for-agent

## Parent

`.scratch/live-preview/idea.md`

## What to build

A **Bore Preview** while the dialog is open (decisions below):

- Handle the command's `executePreview` event (register it in `CommandCreatedHandler`,
  `core/tm_ui.py`).
- In it, if **Show Preview** is on and a Target Body + at least one Sketch Point are selected:
  1. Copy the Target Body with `TemporaryBRepManager.copy` (before).
  2. Run the same Bore code as OK (factor the per-point loop out of
     `CommandExecuteHandler` in `core/tm_execute.py` so both paths share it — no duplicate
     geometry code). Silent: no message boxes, no Timeline Group, no `[UI State]` save.
  3. Copy the body again (after); removed material = before − after
     (`TemporaryBRepManager.booleanOperation`, difference).
  4. Draw the removed material in a CustomGraphicsGroup: red, `setOpacity(0.4, True)`.
- `isValidResult` stays False: OK runs the normal execute path again (D5).
- New dialog checkbox **Show Preview**, default on, remembered in `config.ini` `[UI State]`
  as `show_preview = True`.

## Acceptance criteria

- [ ] With body + Sketch Points selected, the removed material shows translucent red, and the
      body shows the cut (manual smoke).
- [ ] Chamfer, Bottom Radius and Ridges are visible in the preview and match the OK result,
      including on a slanted entry face (manual smoke).
- [ ] Preview updates on size / Bore Type / hole type / Chamfer / Bottom Radius / selection
      change (manual smoke).
- [ ] Through Hole preview cuts all the way through (manual smoke).
- [ ] A point that cannot be bored shows no red shape and no popup; OK still reports it
      (manual smoke).
- [ ] Show Preview off → no preview; setting survives a dialog restart (manual smoke).
- [ ] Cancel leaves nothing in the design or timeline; OK leaves only the normal features in
      one Timeline Group, no custom graphics (manual smoke).
- [ ] Speed with ~20 points is acceptable (manual smoke; if not, file a follow-up issue).
- [ ] Unit test: `show_preview` read/write in `[UI State]`.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md`, `Readme.md`, `resources/help.html` updated.

## Blocked by

None — can start immediately.

## Decisions taken during /grill-me on 2026-11-09

### D1. The preview shows the exact shape

Chamfer, Bottom Radius and Ridges are part of the preview. A preview should not cheat the
user. (A cylinder-only first step was accepted as a fallback, but D2 makes it unnecessary.)

### D2. Real cut in `executePreview`, removed material drawn red

The preview runs the same Bore code as OK; Fusion rolls the features back when the preview
ends. The removed material (body before − body after) is drawn translucent red, like Fusion's
own Extrude Cut preview. Rejected: hand-built `TemporaryBRepManager` shapes — they are wrong
on slanted / curved entry faces and when Fusion fails to make the Chamfer. Cost: the full cut
re-runs on every input change.

### D3. "Show Preview" checkbox

On by default, remembered in `[UI State]`. Escape hatch if large designs get slow.

### D4. Silent preview

A Bore that fails in the preview shows no red shape. No message box during the preview;
errors are reported only on OK.

### D5. OK re-runs the normal execute path

`isValidResult` stays False. Keeps the custom graphics out of the design and leaves the
Timeline Group and the OK message unchanged. (Decided by the agent.)

### D6. Fixed colour

Red, opacity 0.4. A config setting can come later if wanted. (Decided by the agent.)

### Assumptions to verify in Fusion

- Custom graphics drawn in `executePreview` are removed with the preview.
- `TemporaryBRepManager.copy` + boolean difference is fast enough per change.
- Through Hole depth uses the existing `findDistanceThroughBody` (pure query, no features).

## Implementation Summary

<Filled at issue close.>
