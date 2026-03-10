@echo off
REM Delete old tm_*.py files from root (they're now in core/)
cd /d "%~dp0"
del /q tm_state.py tm_config.py tm_helpers.py tm_geometry.py tm_execute.py tm_ui.py 2>nul
echo Old files deleted.
