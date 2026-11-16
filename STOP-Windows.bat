@echo off
REM ===== SecuRAX - double-click to stop everything and free memory =====
REM Runs ./securax down. Your data stays; START-HERE-Windows.bat brings it back.
setlocal EnableExtensions DisableDelayedExpansion
title SecuRAX - stop
set "LOG=%LOCALAPPDATA%\SecuRAX\last-run.log"
if not exist "%~dp0securax.cmd" goto nofiles
echo.
echo   Stopping SecuRAX...
echo.
call "%~dp0securax.cmd" down
if errorlevel 1 goto failed
echo.
echo   Stopped. Memory freed. Your data is kept.
echo.
pause
exit /b 0

:nofiles
if not exist "%LOCALAPPDATA%\SecuRAX\" mkdir "%LOCALAPPDATA%\SecuRAX" >nul 2>&1
2>nul (echo STOP-Windows.bat: securax.cmd is not next to this file: "%~dp0")>"%LOG%"
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
echo   SecuRAX could not stop cleanly. The message above says why.
echo   Next step:  double-click WHATS-WRONG-Windows.bat (it says what stopped and why, in plain words).
echo   A log of this run:  %LOG%
echo.
pause
exit /b 1
