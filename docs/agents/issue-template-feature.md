# <Feature title — what the change delivers>

Status: ready-for-agent

## Parent

<Optional. Feature slug, PRD, or parent issue. Link related issues by path.>

## What to build

<The change, smallest coherent slice first. Files/functions with `path:line`. Reuse
existing helpers — name them. State what is NOT changed. Note if CONTEXT.md needs a new
term or an ADR is warranted.>

## Decisions baked in (from /grill-with-docs on <YYYY-MM-DD>)

<Optional. `### D<N>. Short title` blocks. Omit if no grilling session happened.>

## Acceptance criteria

- [ ] <Observable outcome — a check that fails before and passes after.>
- [ ] <Unit tests for the Fusion-free logic.>
- [ ] <`python -m pytest -q` passes.>
- [ ] <Manual Fusion smoke: the steps to check in Fusion.>
- [ ] <Docs: changelog / Readme / help.html updated if user-visible.>

## Blocked by

<Issues that must land first, or "None — can start immediately.">

## Implementation Summary

<Filled at issue close, in the same commit that flips Status to `completed`.>

**Completed:** <YYYY-MM-DD>, commit <SHA>

- <What was built>
- <Tests added>
- <Test results>
- <Manual Fusion smoke done>
