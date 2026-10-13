@echo off
REM SecuRAX on Windows:  .\securax.cmd up | down | update | doctor | providers add | verify ...
REM `securax` is a bash script, so this runs it inside WSL (Ubuntu) -- the supported way on Windows.
setlocal
where wsl >nul 2>&1
if errorlevel 1 (
  echo.
  echo   SecuRAX needs WSL ^(Windows Subsystem for Linux^). One-time: open PowerShell as Administrator, run
  echo       wsl --install
  echo   restart, then re-run this command.
  exit /b 1
)
REM Strip any Windows line-endings that would break the bash script.
wsl --cd "%~dp0." -e perl -pi -e "s/\r$//" securax
wsl --cd "%~dp0." -e docker info >nul 2>&1
if errorlevel 1 (
  echo.
  echo   Docker isn't reachable from WSL. Fix, once:
  echo     1. Start Docker Desktop and wait for the whale to go steady.
  echo     2. Docker Desktop ^> Settings ^> Resources ^> WSL integration ^> turn ON for "Ubuntu" ^> Apply.
  echo   Then re-run this command.
  exit /b 1
)
wsl --cd "%~dp0." -e bash ./securax %*
exit /b %errorlevel%
