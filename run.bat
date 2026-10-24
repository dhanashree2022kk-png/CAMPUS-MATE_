@echo off
setlocal
cd /d "%~dp0"
title CampusMate
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_and_run.bat first.
  pause
  exit /b 1
)
if not exist "instance\campusmate.db" (
  ".venv\Scripts\python.exe" init_db.py
  if errorlevel 1 (pause & exit /b 1)
)
echo CampusMate: http://127.0.0.1:5000
echo Press Ctrl+C to stop.
".venv\Scripts\python.exe" app.py
endlocal
