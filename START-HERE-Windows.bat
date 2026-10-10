@echo off
REM ===== SecuRAX - double-click to start everything on Windows =====
REM One step. Needs Docker Desktop running (the green whale in the system tray).
title SecuRAX
echo.
echo   Starting SecuRAX...  (this is the only step - just wait)
echo.
cd /d "%~dp0local\compose"
if not exist .env copy .env.example .env >nul

REM 1) Bring the whole estate up.
docker compose --profile ai up -d --build

REM 2) Open your home screen RIGHT NOW so you are never left staring at a terminal.
REM    The AI switches on by itself once the one-time model download finishes.
echo.
echo   Opening your home screen: http://localhost:8088
timeout /t 3 >nul
start "" http://localhost:8088

REM 3) Download the local model in the BACKGROUND (first run only, ~1 GB).
REM    The home screen's "Ask" tab shows a live "AI is ready / warming up" status,
REM    so you always know what is happening - no documentation needed.
echo.
echo   Downloading the local AI model in the background (first run only, ~2-5 min).
echo   You can start using the planner, playbook and life-OS immediately.
start "SecuRAX model download" /min cmd /c "timeout /t 6 >nul & docker compose --profile ai exec -T ollama ollama pull qwen2.5:1.5b & docker compose --profile ai exec -T ollama ollama pull llama-guard3:1b"

echo.
echo   Done. Home screen: http://localhost:8088
echo   To stop later and free memory: double-click STOP-Windows.bat
echo.
pause
