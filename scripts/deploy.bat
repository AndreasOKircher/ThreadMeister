@echo off
:: deploy.bat – Deploy ThreadMeister to the Fusion 360 AddIns folder
::
:: Usage:
::   deploy.bat          deploy to Fusion 360 AddIns folder
::   deploy.bat /preview preview what would be copied (dry run)

setlocal

:: Source is the project root (one level up from this scripts\ folder)
pushd "%~dp0.."
set "SOURCE=%CD%\"
popd

set "TARGET=%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\ThreadMeister"

:: Check for dry-run flag
set DRYRUN=0
if /i "%1"=="/preview" set DRYRUN=1

echo.
echo ThreadMeister Deploy
echo   Source : %SOURCE%
echo   Target : %TARGET%
echo.

if %DRYRUN%==1 (
    echo [DRY RUN - no files will be changed]
    echo.
)

:: Create target folder if it doesn't exist
if not exist "%TARGET%\" (
    if %DRYRUN%==0 mkdir "%TARGET%"
    echo   Created  target folder
)

:: ── Copy Python modules and manifests ────────────────────────────────────────
call :CopyFile "ThreadMeister.py"
call :CopyFileInDir "core" "tm_state.py"
call :CopyFileInDir "core" "tm_config.py"
call :CopyFileInDir "core" "tm_helpers.py"
call :CopyFileInDir "core" "tm_geometry.py"
call :CopyFileInDir "core" "tm_execute.py"
call :CopyFileInDir "core" "tm_ui.py"
call :CopyFileInDir "core" "__init__.py"
call :CopyFile "ThreadMeister.manifest"
call :CopyFile "manifest.json"
call :CopyFile "License.txt"
call :CopyFile "Readme.md"

:: ── config.ini: only copy if not already present (preserve custom settings) ──
if exist "%TARGET%\config.ini" (
    echo   Skipped  config.ini  ^(already exists - custom settings preserved^)
) else (
    if exist "%SOURCE%config.ini" (
        if %DRYRUN%==0 xcopy /y /q "%SOURCE%config.ini" "%TARGET%\" >nul
        echo   Copied   config.ini  ^(first deploy^)
    )
)

:: ── Copy icons folder ─────────────────────────────────────────────────────────
if exist "%SOURCE%resources\icons\" (
    if %DRYRUN%==0 (
        if not exist "%TARGET%\resources\icons\" mkdir "%TARGET%\resources\icons"
        xcopy /y /q /e "%SOURCE%resources\icons\*" "%TARGET%\resources\icons\" >nul
    )
    echo   Copied   resources\icons\
) else (
    echo   MISSING  resources\icons\
)

echo.
if %DRYRUN%==1 (
    echo Dry run complete. No files were changed.
) else (
    echo Done. Reload the add-in in Fusion 360:
    echo   Scripts and Add-Ins ^> ThreadMeister ^> Run
)
echo.
goto :eof

:: ── Helper: copy a single file ────────────────────────────────────────────────
:CopyFile
if not exist "%SOURCE%%~1" (
    echo   MISSING  %~1
    goto :eof
)
if %DRYRUN%==0 xcopy /y /q "%SOURCE%%~1" "%TARGET%\" >nul
echo   Copied   %~1
goto :eof

:: ── Helper: copy a file from a subdirectory ─────────────────────────────────────
:CopyFileInDir
set "SUBDIR=%~1"
set "FILENAME=%~2"
if not exist "%SOURCE%%SUBDIR%\%FILENAME%" (
    echo   MISSING  %SUBDIR%\%FILENAME%
    goto :eof
)
if not exist "%TARGET%\%SUBDIR%\" (
    if %DRYRUN%==0 mkdir "%TARGET%\%SUBDIR%"
)
if %DRYRUN%==0 xcopy /y /q "%SOURCE%%SUBDIR%\%FILENAME%" "%TARGET%\%SUBDIR%\" >nul
echo   Copied   %SUBDIR%\%FILENAME%
goto :eof
