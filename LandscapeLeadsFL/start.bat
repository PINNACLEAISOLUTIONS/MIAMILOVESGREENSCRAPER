@echo off
echo Starting LandscapeLeadsFL Lead Intelligence Suite...

:: Check if virtual env exists, else use global python
set PYTHON_CMD=python

echo.
echo [1/2] Running Discovery Scout...
%PYTHON_CMD% main.py

echo.
echo [2/2] Launching Intelligence Dashboard...
start cmd /k "cd dashboard && %PYTHON_CMD% app.py"

echo.
echo Dashboard is launching!
echo View leads at: http://localhost:5005
echo.
pause
