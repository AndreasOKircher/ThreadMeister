# live-preview

Draw a translucent cylinder at each selected Sketch Point with Fusion's CustomGraphics API
while the dialog is open, updating when insert size / hole type changes — like Fusion's own
Hole command. Catches "wrong size selected" before anything hits the timeline.

## Open questions

- ~~CustomGraphics vs the command's `executePreview` event?~~ Decided 2026-11-09, see below.
- Preview of Chamfer and Bottom Radius: build them as temporary geometry too, or show only the cylinder?
- Preview depth for Through Holes without computing the through distance?
- Performance with many points.

## Decision 2026-11-09: CustomGraphics, red translucent

The user wants the look of Fusion's own cut tool body: translucent red, shown as soon as body
and Sketch Points are selected. Chosen approach:

- Build each Bore as a temporary body with `TemporaryBRepManager` (cylinder; later Chamfer /
  Bottom Radius).
- Draw it with `CustomGraphicsGroup.addBRepBody`, red solid colour, `setOpacity(~0.4, True)`.
- Redraw in the command's `executePreview` event (fires on every selection / input change).
  `isValidResult` stays False, so OK still runs the normal execute path.
- The body is not changed until OK.

Rejected: running the real Bore code in `executePreview` (shows the finished cut, not a red tool
body; slower with many points).

Assumption: speed and look must be confirmed by a smoke test in Fusion.

API refs:
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomGraphicsBRepBody_setOpacity.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomGraphicsGroup.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TemporaryBRepManager_Sample.htm

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
