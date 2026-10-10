@echo off
REM ===== SecuRAX — double-click to start everything on Windows =====
REM Needs Docker Desktop installed and running (the green whale in the system tray).
title SecuRAX
echo Starting SecuRAX... (first run downloads a model, be patient)
cd /d "%~dp0local\compose"
if not exist .env copy .env.example .env >nul
docker compose --profile ai up -d --build
echo.
echo Opening your Guiding Map home screen...
timeout /t 6 >nul
start "" http://localhost:8088
echo.
echo Done. Your home screen: http://localhost:8088
echo To stop later: run STOP-Windows.bat
pause
