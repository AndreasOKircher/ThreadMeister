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
:: All files go into a ThreadMeister\ root folder inside the zip.
:: Entry paths use '/' (zip standard); Compress-Archive in PowerShell 5.1 writes '\',
:: which macOS unzips as flat files named "ThreadMeister\core\..."
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
  "Copy-Item (Join-Path $root 'core\tm_ridge.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_preview.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_ui.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'core\tm_debug_export.py') (Join-Path $pkg 'core');" ^
  "Copy-Item (Join-Path $root 'resources\icons\*') (Join-Path $pkg 'resources\icons');" ^
  "Copy-Item (Join-Path $root 'resources\help.html') (Join-Path $pkg 'resources');" ^
  "Copy-Item (Join-Path $root 'ThreadMeister.png') $pkg;" ^
  "Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem;" ^
  "$za = [System.IO.Compression.ZipFile]::Open($zip, 'Create');" ^
  "Get-ChildItem $pkg -Recurse -File | ForEach-Object {" ^
  "  $name = 'ThreadMeister/' + $_.FullName.Substring($pkg.Length + 1).Replace('\', '/');" ^
  "  [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($za, $_.FullName, $name) };" ^
  "$za.Dispose();" ^
  "Remove-Item $tmp -Recurse -Force;" ^
  "Write-Host ('  Created  ' + $zip)"

echo.
echo Done. Zip is ready at:
echo   %ZIPFILE%
echo.
