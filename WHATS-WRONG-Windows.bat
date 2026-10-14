@echo off
REM ===== SecuRAX - double-click when something is not working =====
REM Shows what is running, what stopped and why, in plain words. Copy the window's text into the chat if it is still unclear.
title SecuRAX - what is wrong?
call "%~dp0securax.cmd" why
echo.
pause
