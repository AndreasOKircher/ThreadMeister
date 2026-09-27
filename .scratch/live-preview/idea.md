# live-preview

Draw a translucent cylinder at each selected Sketch Point with Fusion's CustomGraphics API
while the dialog is open, updating when insert size / hole type changes — like Fusion's own
Hole command. Catches "wrong size selected" before anything hits the timeline.

## Open questions

- CustomGraphics vs the command's `executePreview` event (real features, rolled back automatically)?
- Preview depth for Through Holes without computing the through distance?
- Performance with many points.

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
