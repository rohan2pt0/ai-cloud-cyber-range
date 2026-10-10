@echo off
title SecuRAX - stop
cd /d "%~dp0local\compose"
docker compose --profile ai down
echo Stopped. RAM freed.
pause
