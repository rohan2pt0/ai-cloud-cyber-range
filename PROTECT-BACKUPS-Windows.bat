@echo off
REM ===== SecuRAX - double-click to protect (encrypt) your backups =====
REM One guided step: it makes a key, asks where to keep a second copy (a USB stick is best), switches encryption on and proves it works.
title SecuRAX - protect your backups
call "%~dp0securax.cmd" protect
echo.
pause
