# ridge-thread: where we stopped (2026-11-07)

## State

- Branch: `ridge-thread-r1` (cut from local `master`). Not pushed. `master` has unpushed
  docs commits too.
- Issue 01 (`issues/01-ridge-thread-bore.md`): code done, commit `4b98bc3`,
  `Status: ready-for-human`. 137 tests pass. **Fusion smoke test still open.**
- Issue 02 (lead-in chamfer) and issue 03 (icons, docs, credits): `on-branch`, not started.
- Untracked files not from this work (left alone): `resources/images/Title_RidgeThread*.png`,
  `.scratch/ridge-thread/make_title*.py`, `Title mode.png`.

## Next: Fusion smoke test for issue 01 (user)

1. On your Windows PC, in the repo folder, run: `scripts\deploy.bat`
2. In Fusion, restart the ThreadMeister add-in.
3. Make a Ridge Thread for M3, M4 and M5, blind and through. Use a sketch on a construction
   plane and a sketch on a body face.
4. Look at a section view: M3 and M4 have 3 ridges, M5 has 4. Inner Ø 2.40 / 3.50 / 4.50.
5. Move a Sketch Point. The Ridge Thread must move with it.
6. Make one Heat-Set Insert bore. It must work as before.
7. Tell Claude what you see. If there is an error, paste the error text.

## After the smoke test (Claude)

- Smoke OK → flip issue 01 to `completed` (small commit), then start issue 02 with `/tdd`.
- Smoke fails → fix on `ridge-thread-r1` (`/diagnose` if unclear).
- All 3 issues done → `/finish-feature`.

## Choices made by Claude (user may still change them; see PRD.md)

1. Ridge Ø follows the inner Ø; the arc distance stays fixed.
2. Depth resets to 4 × D on size change; not remembered.
3. Last Bore Type and last Ridge Thread size are remembered.
4. First ridge on the sketch x axis (as the fork).
5. If the lead-in chamfer fails (issue 02): keep the bore, show a warning.
