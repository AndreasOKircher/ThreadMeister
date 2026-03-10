@echo off
REM Setup script for test environment

echo Creating virtual environment...
python -m venv .venv

echo.
echo Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
pip install -q -r requirements-dev.txt

echo.
echo Running tests...
python -m pytest tests/ -v --tb=short

echo.
echo Done! To manually run tests later:
echo   1. .venv\Scripts\activate.bat
echo   2. pytest
