@echo off
REM ===== SecuRAX - double-click to start everything on Windows =====
REM One step. Needs Docker Desktop running (the green whale in the system tray).
title SecuRAX
setlocal
echo.
echo   Starting SecuRAX...  (this is the only step - just wait)
echo.
cd /d "%~dp0local\compose"
if not exist .env copy .env.example .env >nul

REM Surface the product version at runtime.
for /f "usebackq delims=" %%v in ("%~dp0VERSION") do set SECURAX_VERSION=%%v

REM 1) Bring the whole estate up.
docker compose --profile ai up -d --build

REM 2) Open your Command Center RIGHT NOW - ONE page that links every app (no URLs to remember).
echo.
echo   Opening your Command Center: http://localhost:8088/portal/hub.html
timeout /t 3 >nul
start "" http://localhost:8088/portal/hub.html

REM 3) (Optional) For INSTANT answers, paste a free Google AI Studio key into local\compose\.env
REM    as  GEMINI_API_KEY=your-key  and re-run this file. Without it, the slower private local
REM    model is used. The local model downloads in the BACKGROUND (first run only, ~1 GB).
echo.
echo   TIP: for instant answers, put a free Gemini key in local\compose\.env (GEMINI_API_KEY=...)
echo        Get one free at https://aistudio.google.com/apikey  then re-run this file.
echo.
echo   Downloading the private local model in the background (first run only; not needed to start).
start "SecuRAX model download" /min cmd /c "timeout /t 6 >nul & docker compose --profile ai exec -T ollama ollama pull qwen2.5:1.5b"

echo.
echo   Done. Command Center: http://localhost:8088/portal/hub.html
echo   To stop later and free memory: double-click STOP-Windows.bat
echo.
pause
