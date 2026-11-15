@echo off
setlocal
cd /d "%~dp0"
py -3 --version >nul 2>&1
if not errorlevel 1 (
  py -3 -m lab serve --open
) else (
  python --version >nul 2>&1
  if errorlevel 1 (
    echo Python was not found. Install Python 3.11 or newer, then try again.
    pause
    exit /b 1
  )
  python -m lab serve --open
)
if errorlevel 1 pause
