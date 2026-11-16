@echo off
REM ===== SecuRAX - double-click to start everything on Windows =====
REM Needs WSL (Ubuntu) and Docker. Runs ./securax go: start, update, schedules, phones, backup and sync, then one status screen.
setlocal EnableExtensions DisableDelayedExpansion
title SecuRAX
set "LOG=%LOCALAPPDATA%\SecuRAX\last-run.log"
if not exist "%~dp0securax.cmd" goto nofiles
echo.
echo   Starting SecuRAX. This is the only step: just wait. The first run downloads images and can take a while.
echo.
call "%~dp0securax.cmd" go
if errorlevel 1 goto failed
echo.
echo   Done. Your Command Center opens in your browser. If it did not, run:  .\securax.cmd open
echo.
echo   Tip: for instant answers add a free key:  .\securax.cmd providers add
echo   To protect (encrypt) your backups: double-click PROTECT-BACKUPS-Windows.bat
echo   To stop later and free memory: double-click STOP-Windows.bat
echo.
pause
exit /b 0

:nofiles
if not exist "%LOCALAPPDATA%\SecuRAX\" mkdir "%LOCALAPPDATA%\SecuRAX" >nul 2>&1
2>nul (echo START-HERE-Windows.bat: securax.cmd is not next to this file: "%~dp0")>"%LOG%"
echo.
echo   This file only works inside the SecuRAX folder, next to securax.cmd. It is here now:
echo       "%~dp0"
echo   Next step:  if you opened it from a ZIP, right-click the ZIP, choose "Extract All", open the extracted
echo   folder and double-click this file there. To start it from the Desktop, make a shortcut, not a copy.
echo   A log of this run:  %LOG%
echo.
pause
exit /b 1

:failed
echo.
echo   SecuRAX did not start. The message above says why.
echo   Next step:  double-click WHATS-WRONG-Windows.bat (it says what stopped and why, in plain words).
echo   A log of this run:  %LOG%
echo.
pause
exit /b 1
