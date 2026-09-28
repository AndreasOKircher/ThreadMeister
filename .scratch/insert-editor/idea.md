# insert-editor

Custom inserts need hand-editing `config.ini` (there is a placeholder
`Custom = 1.0, 2.0, 3.0`). A small dialog with add / edit / delete removes the most error-prone
manual step and avoids syntax errors breaking config loading.

## Open questions

- Separate command, or a button inside the main dialog?
- Validation rules (diameter > 0, length > 0, unique names)?
- Should it also edit vendor presets (see vendor-presets) or only custom entries?
- Remove the `Custom = 1.0, 2.0, 3.0` placeholder?

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
