@echo off
setlocal
cd /d "%~dp0"
title CampusMate Setup and Run
echo.
echo ========================================
echo     CampusMate - First-time Setup
echo ========================================
echo.
set "PYTHON_CMD="
where py >nul 2>nul
if %errorlevel%==0 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo ERROR: Python 3 was not found.
  echo Install Python 3.10 or newer from https://www.python.org/downloads/windows/
  echo Enable "Add python.exe to PATH", then reopen VS Code and retry.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating virtual environment...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto failed
) else (echo [1/4] Existing virtual environment found.)
set "PY=.venv\Scripts\python.exe"
echo [2/4] Installing dependencies. Internet is needed for first setup.
"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto failed
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo [3/4] Initializing database and demo records; existing data is preserved.
"%PY%" init_db.py
if errorlevel 1 goto failed
"%PY%" seed_data.py
if errorlevel 1 goto failed
echo [4/4] Starting CampusMate...
echo Website: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server.
echo.
"%PY%" app.py
goto end
:failed
echo.
echo Setup failed. Check the error above, Python installation and internet connection, then retry.
pause
exit /b 1
:end
endlocal
