# ThreadMeister

Project instructions for coding agents working in this repository.

## Purpose

ThreadMeister is an Autodesk Fusion add-in (Python) that cuts heat-set Insert Bores at
selected Sketch Points: blind or through holes, optional Chamfer and Bottom Radius, all
grouped in one Timeline Group. The Insert Library lives in `config.ini`.

## Communication style

Be concise. Propose the specific fix directly instead of long exploratory write-ups.

## Accuracy / ground truth

Verify behaviour in the code before asserting it. Fusion API behaviour can change between
Fusion releases (see ADR-0002) — anything that only Fusion can confirm must be stated as an
assumption and verified by a manual smoke test in Fusion.

## Source of truth

- Domain language: `CONTEXT.md`
- Architecture, execution flow, config format: `docs/development-notes.md`
- Decisions: `docs/adr/`
- Agent issue workflow: `docs/agents/issue-tracker.md`
- Issue templates: `docs/agents/issue-template-bug.md`, `docs/agents/issue-template-feature.md`
- Triage labels: `docs/agents/triage-labels.md`
- User-facing docs: `Readme.md`, `resources/help.html`, `docs/changelog.md`

If an instruction here conflicts with those docs, follow the docs and state the conflict.

## Repository layout

- `ThreadMeister.py` — add-in entry point (`run()` / `stop()`).
- `core/` — all logic, one module per concern (`tm_execute.py` hole loop, `tm_geometry.py`
  geometry, `tm_ui.py` dialog, `tm_config.py` config I/O, `tm_state.py` shared state).
- `tests/` — pytest suite. Runs **without Fusion**: `tests/conftest.py` stubs the `adsk`
  module before any import.
- `scripts/` — `deploy.bat` (copy into Fusion's AddIns folder), `package.bat` (App Store zip),
  fixture/profile inspectors.
- Project skills: `.agents/skills/<skill-name>/`. Load with the `Skill` tool before use.
- Feature workspaces: `.scratch/<feature-slug>/`.

## Terminology rules

Use the canonical names from `CONTEXT.md`. Don't invent synonyms (e.g. say **Bore**, not
"hole cut"; **Insert Spec**, not "insert data").

## Gotchas

- **Fusion API cannot be unit-tested for real.** `adsk` is a `MagicMock` in tests. Pure logic
  (depth maths, config parsing, profile filters) gets unit tests; anything that calls Fusion
  needs a manual smoke test in Fusion, listed in the issue's acceptance criteria.
- **MagicMock auto-creates attributes.** `hasattr(mock, 'x')` is always true — use
  `isinstance` checks to tell mocks from real collections (see `tests/test_profile_selection.py`).
- **`Sketch.referencePlane` is unsafe for sketches on a body face** (Fusion changed it after
  March 2026 — GitHub issue #1, ADR-0002). Don't add new calls to it.
- **Units:** Fusion's API works in **cm**; Insert Specs and `config.ini` are in **mm**.
  Convert at the call site (`/ 10.0`).
- **The installed add-in is not your working copy.** Fusion runs whatever is in its AddIns /
  ApplicationPlugins folder. Deploy with `scripts\deploy.bat` before a smoke test.

## Working style

- Think before coding. State assumptions; if there are several readings, list them.
- Prefer the simplest solution that fits the existing design.
- Implement only what the issue requires. No speculative abstractions.
- When presenting options, give each a short explanation with pros and cons, and recommend one.

## Change discipline

- Touch only what the task needs. Match existing style (camelCase Fusion-facing functions,
  `tm_` module prefix, `try/except` + `messageBox` error reporting).
- Clean up only code your change makes obsolete. No unrelated refactors.
- User-visible change → update `docs/changelog.md` and, if relevant, `Readme.md` /
  `resources/help.html`. Version bumps go in `ThreadMeister.manifest` and `manifest.json`.

## Test loop

```
python -m pytest -q
```

Whole suite runs in about a second. Run it before every commit that touches `core/` or `tests/`.

## Agent workflow

### Feature scratch spaces

Each feature gets `.scratch/<feature-slug>/`:

- `idea.md` — raw notes, user need, open questions.
- `PRD.md` — optional, from `/to-prd`.
- `issues/<NN>-<slug>.md` — implementation issues, numbered from `01`.
- `.feature-status.md` — branch tracker, seeded by `/start-feature`.

A `<feature-slug>` is short, lowercase, hyphen-separated. Everything for one feature stays in
its folder. Details: `docs/agents/issue-tracker.md`.

### GitHub issues

User reports arrive as GitHub issues. Mirror each accepted one into a `.scratch/` bug issue
that links back to the GitHub issue; the `.scratch/` file is where the work is tracked.

### Branch workflow (per feature)

- **One feature → one branch `<slug>-rN`**, cut from local `master`. All of the feature's
  issues are implemented on it. `/start-feature` opens it, `/finish-feature` closes it.
- **Docs escape hatch:** changes that cannot affect the add-in at runtime (`docs/`,
  `.scratch/`, markdown, comments, agent files) go straight to `master`.
- Anything under `core/`, `ThreadMeister.py`, `config.ini`, `resources/`, or `tests/` needs
  a feature branch.
- Extending a shipped feature: add new issue files to the existing folder and cut
  `<slug>-r(N+1)`. Never reopen a terminal issue — file a new one.

### Commit policy (overrides Claude Code's default)

- When an issue is implemented and tests pass, commit without asking, on the feature branch.
  One commit per issue close, bundling the code, the `Status: completed` flip, and the
  `## Implementation Summary`.
- Stage selectively — only the issue's files. Never `git add -A`.
- **Always ask before:** `git push`, force-push, history rewrites, deleting branches outside
  `/finish-feature`.
- Skip the commit when tests fail or the issue is parked (`needs-info`, `ready-for-human`).

### Triage labels

See `docs/agents/triage-labels.md`.

### Skills

The Matt Pocock skills (`/grill-me`, `/grill-with-docs`, `/to-prd`, `/to-issues`, `/tdd`,
`/diagnose`, `/triage`, …) are installed per user under `~/.claude/skills/`. Project skills
live in `.agents/skills/`: `start-feature`, `finish-feature`. If a skill name matches what
the user typed, invoke it.
