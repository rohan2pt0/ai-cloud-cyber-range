@echo off
title SecuRAX - stop
call "%~dp0securax.cmd" down
echo Stopped. RAM freed.
pause
