# ci-setup

There are 60+ pytest tests with no Fusion dependency and a `pytest.ini`, but no
`.github/workflows/`. A workflow running pytest on push/PR protects the tests and adds a
badge to the README.

Note: `requirements-dev.txt` is a full local conda freeze with `file:///C:/...` entries — CI
can't install it. CI should install only `pytest` (and `pytest-cov`).

## Open questions

- None.

Source: feature proposals, session "Feature proposals for repo" (2026-06-11); selected 2026-09-27.
