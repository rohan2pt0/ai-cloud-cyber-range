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
echo   Your Command Center opens in your browser. If it did not, double-click START again or run:  .\securax.cmd open
echo.
echo   Tip: for instant answers add a free key:  .\securax.cmd providers add
echo   To protect (encrypt) your backups: double-click PROTECT-BACKUPS-Windows.bat
echo   To stop later and free memory: double-click STOP-Windows.bat
echo.
pause
