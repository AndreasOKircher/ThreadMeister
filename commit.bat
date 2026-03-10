@echo off
REM Commit Phase 1b & 1c work
git add -A
git commit -m "Phase 1b & 1c: move modules to core/, refactor findProfileForCircle into sub-functions - Update version to 1.1.0b - All features tested and verified in Fusion 360 - Ready for Phase 2"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Commit successful!
    git log --oneline -1
) else (
    echo Commit failed with error %ERRORLEVEL%
)
