@echo off
REM Build script for Complex Unzip Tool v2
REM This script builds the EXE using Poetry and PyInstaller

echo Building Complex Unzip Tool v2...
echo.

REM Check if Poetry is available
poetry --version >nul 2>&1
if errorlevel 1 (
    echo Error: Poetry not found. Please install Poetry first.
    echo Visit: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)

REM Install dependencies including PyInstaller
echo Installing dependencies...
poetry install

REM Run the build script
echo.
echo Building executable...
poetry run python build_exe.py

echo.
echo Build complete! Check the 'dist' directory for your executable.
pause
