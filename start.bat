@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 serve.py
  if errorlevel 1 pause
  exit /b
)

where python >nul 2>nul
if not errorlevel 1 (
  python serve.py
  if errorlevel 1 pause
  exit /b
)

echo.
echo Python 3 was not found in PATH.
echo Install Python on D: or E: and select "Add Python to PATH".
echo.
pause
exit /b 1
