@echo off
REM ===== SecuRAX — double-click to start everything on Windows =====
REM Needs Docker Desktop installed and running (the green whale in the system tray).
title SecuRAX
echo Starting SecuRAX... (first run downloads a model, be patient)
cd /d "%~dp0local\compose"
if not exist .env copy .env.example .env >nul
docker compose --profile ai up -d --build
echo.
echo Pulling the local model (one-time, ~1 GB)... this can take a few minutes.
timeout /t 8 >nul
docker compose --profile ai exec -T ollama ollama pull qwen2.5:1.5b
docker compose --profile ai exec -T ollama ollama pull llama-guard3:1b
echo.
echo Opening your Guiding Map home screen...
timeout /t 4 >nul
start "" http://localhost:8088
echo.
echo Done. Your home screen: http://localhost:8088
echo To stop later: run STOP-Windows.bat
pause
