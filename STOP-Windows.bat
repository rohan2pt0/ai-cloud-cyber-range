@echo off
title SecuRAX - stop
call "%~dp0securax.cmd" down
if errorlevel 1 (
  echo.
  echo   Could not stop - read the message above.
) else (
  echo Stopped. RAM freed.
)
pause
