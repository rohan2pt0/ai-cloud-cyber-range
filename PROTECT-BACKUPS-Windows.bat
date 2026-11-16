@echo off
REM ===== SecuRAX - double-click to protect (encrypt) your backups =====
REM One guided step: it makes a key, asks where to keep a second copy (a USB stick is best), switches encryption on and proves it works.
setlocal EnableExtensions DisableDelayedExpansion
title SecuRAX - protect your backups
set "LOG=%LOCALAPPDATA%\SecuRAX\last-run.log"
if not exist "%~dp0securax.cmd" goto nofiles
echo.
echo   Protecting your backups. Answer the questions as they come.
echo.
call "%~dp0securax.cmd" protect
if errorlevel 1 goto failed
echo.
echo   Done. Keep the second copy of the key somewhere safe: without it an encrypted backup cannot be opened.
echo.
pause
exit /b 0

:nofiles
if not exist "%LOCALAPPDATA%\SecuRAX\" mkdir "%LOCALAPPDATA%\SecuRAX" >nul 2>&1
2>nul (echo PROTECT-BACKUPS-Windows.bat: securax.cmd is not next to this file: "%~dp0")>"%LOG%"
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
echo   Backup protection did not finish. Nothing was switched on half-way. The message above says why.
echo   Next step:  double-click WHATS-WRONG-Windows.bat (it says what stopped and why, in plain words).
echo   A log of this run:  %LOG%
echo.
pause
exit /b 1
