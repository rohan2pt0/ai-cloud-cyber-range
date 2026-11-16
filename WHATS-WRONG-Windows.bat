@echo off
REM ===== SecuRAX - double-click when something is not working =====
REM Shows what is running, what stopped and why, in plain words. Copy the window's text into the chat if it is still unclear.
setlocal EnableExtensions DisableDelayedExpansion
title SecuRAX - what is wrong?
set "LOG=%LOCALAPPDATA%\SecuRAX\last-run.log"
if not exist "%~dp0securax.cmd" goto nofiles
echo.
echo   Checking what is running, what stopped and why...
echo.
call "%~dp0securax.cmd" why
if errorlevel 1 goto failed
echo.
echo   That is everything SecuRAX can see. Still unclear? Copy this window's text into the chat.
echo.
pause
exit /b 0

:nofiles
if not exist "%LOCALAPPDATA%\SecuRAX\" mkdir "%LOCALAPPDATA%\SecuRAX" >nul 2>&1
2>nul (echo WHATS-WRONG-Windows.bat: securax.cmd is not next to this file: "%~dp0")>"%LOG%"
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
echo   The check itself could not finish. The message above says why.
echo   Next step:  follow the "Next step" printed above. Still stuck? Copy this window's text into the chat.
echo   A log of this run:  %LOG%
echo.
pause
exit /b 1
