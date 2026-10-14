@echo off
REM ===== SecuRAX - double-click to get the latest version (safe: it backs up first and rolls back if the new version does not start) =====
title SecuRAX - update
call "%~dp0securax.cmd" update
echo.
pause
