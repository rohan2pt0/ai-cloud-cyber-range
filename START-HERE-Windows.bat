@echo off
REM ===== SecuRAX - double-click to start everything on Windows =====
REM Needs Docker Desktop running + WSL (Ubuntu). Runs the same ./securax up as Mac/Linux.
title SecuRAX
setlocal
echo.
echo   Starting SecuRAX...  (this is the only step - just wait; first run downloads images)
echo.
call "%~dp0securax.cmd" up
if errorlevel 1 (
  echo.
  echo   Something needs attention - read the message above.
  pause
  exit /b 1
)
echo.
echo   Opening your Command Center: http://localhost:8088/hub.html
start "" http://localhost:8088/hub.html
echo.
echo   Tip: for instant answers add a free key:  .\securax.cmd providers add
echo   To stop later and free memory: double-click STOP-Windows.bat
echo.
pause
