# live-preview

Show the Bores while the dialog is open, before OK: the material that will be removed appears
translucent red, like Fusion's own Extrude Cut preview. Catches "wrong size / wrong point /
wrong depth" before anything hits the timeline.

## Open questions

All resolved in the /grill-with-docs session of 2026-11-09 — see the decision record in
[issues/01-custom-graphics-preview.md](issues/01-custom-graphics-preview.md).

## History

- 2026-11-09 (earlier the same day): first choice was hand-built `TemporaryBRepManager`
  cylinders drawn as CustomGraphics. Replaced in the grill session by D2 (real cut in
  `executePreview` + red removed material), because hand-built shapes cannot match the real
  Chamfer on slanted / curved entry faces or when Fusion fails to make the Chamfer.

API refs:
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomGraphicsBRepBody_setOpacity.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/CustomGraphicsGroup.htm
- https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/TemporaryBRepManager_Sample.htm

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
