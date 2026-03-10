@echo off
REM Commit Phase 2: Test Suite

git add -A
git commit -m "Phase 2: add pytest test suite (v1.1.1) - 49 comprehensive unit tests covering tm_helpers, tm_config, and tm_geometry filter functions - Mock-based testing with zero Fusion 360 dependency - conftest.py handles adsk module stubbing before imports - Includes test infrastructure: pytest.ini, requirements-dev.txt, .venv setup - All tests pass and ready for CI/CD integration"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Commit successful!
    git log --oneline -1
) else (
    echo Commit failed with error %ERRORLEVEL%
)
