# Run pytest on GitHub Actions

Status: ready-for-agent

## Parent

`.scratch/ci-setup/idea.md`

## What to build

Add `.github/workflows/tests.yml`: on push and pull_request, ubuntu-latest, Python 3.12
(Fusion ships 3.12 — check the installed version), `pip install pytest pytest-cov`,
`python -m pytest -q`. Add a status badge to `Readme.md`. Trim `requirements-dev.txt` to the
real test dependencies.

## Acceptance criteria

- [ ] Workflow runs green on a push.
- [ ] Badge in `Readme.md`.
- [ ] `requirements-dev.txt` installs cleanly on Linux.
- [ ] `python -m pytest -q` passes.
- [ ] `docs/changelog.md` updated.

## Blocked by

None — can start immediately.

## Implementation Summary

<Filled at issue close.>
