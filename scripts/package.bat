@echo off
:: package.bat – Create App Store .zip in dist\
::
:: Usage:
::   dist\package.bat

setlocal

:: Source is the project root (one level up from this dist\ folder)
pushd "%~dp0.."
set "ROOT=%CD%"
popd

set "DIST=%ROOT%\dist"
set "ZIPFILE=%DIST%\ThreadMeister.zip"

echo.
echo ThreadMeister Packaging
echo   Source : %ROOT%
echo   Output : %ZIPFILE%
echo.

:: Delete old zip if it exists
if exist "%ZIPFILE%" (
    del "%ZIPFILE%"
    echo   Removed old zip
)

:: Use PowerShell to create the zip with correct folder structure
:: All files go into a ThreadMeister\ root folder inside the zip
powershell -NoProfile -Command ^
  "$root = '%ROOT%';" ^
  "$zip = '%ZIPFILE%';" ^
  "$tmp = Join-Path $env:TEMP 'ThreadMeister_pkg';" ^
  "$pkg = Join-Path $tmp 'ThreadMeister';" ^
  "if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force };" ^
  "New-Item -ItemType Directory -Path $pkg -Force | Out-Null;" ^
  "New-Item -ItemType Directory -Path (Join-Path $pkg 'core') -Force | Out-Null;" ^
  "New-Item -ItemType Directory -Path (Join-Path $pkg 'resources\icons') -Force | Out-Null;" ^
  "Copy-Item (Join-Path $root 'ThreadMeister.py') $pkg;" ^
  "Copy-Item (Join-Path $root 'ThreadMeister.manifest') $pkg;" ^
  "Copy-Item (Join-Path $root 'manifest.json') $pkg;" ^
  "Copy-Item (Join-Path $root 'config.ini') $pkg;" ^
  "Copy-Item (Join-Path $root 'License.txt') $pkg;" ^
  "Copy-Item (Join-Path $root 'Readme.md') $pkg;" ^
  "Copy-Item (Join-Path $root 'core\__init__.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_state.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_config.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_helpers.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_geometry.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_execute.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_ui.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_debug_export.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'resources\icons\*') (Join-Path $pkg 'resources\icons');" ^
  "Copy-Item (Join-Path $root 'ThreadMeister.png') $pkg;" ^
  "Compress-Archive -Path $pkg -DestinationPath $zip -Force;" ^
  "Remove-Item $tmp -Recurse -Force;" ^
  "Write-Host '  Created  $zip'"

echo.
echo Done. Zip is ready at:
echo   %ZIPFILE%
echo.
