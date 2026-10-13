@echo off
REM SecuRAX on Windows:  .\securax.cmd up | down | update | doctor | providers add | verify ...
REM `securax` is a bash script, so this runs it inside WSL (Ubuntu) -- the supported way on Windows.
setlocal
where wsl >nul 2>&1
if errorlevel 1 goto nowsl
REM wsl.exe exists on most Windows 10/11 even with NO distro installed, so check for a real one.
set "DISTRO="
set WSL_UTF8=1
for /f "usebackq delims=" %%d in (`wsl -l -q 2^>nul`) do (
  if not defined DISTRO if /i not "%%d"=="docker-desktop" if /i not "%%d"=="docker-desktop-data" set "DISTRO=%%d"
)
if defined DISTRO set "DISTRO=%DISTRO: =%"
if not defined DISTRO goto nowsl
REM Strip any Windows line-endings that would break the bash script.
wsl -d "%DISTRO%" --cd "%~dp0." -e perl -pi -e "s/\r$//" securax
wsl -d "%DISTRO%" --cd "%~dp0." -e docker info >nul 2>&1
if errorlevel 1 goto nodocker
wsl -d "%DISTRO%" --cd "%~dp0." -e bash ./securax %*
exit /b %errorlevel%

:nowsl
echo.
echo   SecuRAX needs WSL with a Linux distribution (Ubuntu). One-time: open PowerShell as Administrator, run
echo       wsl --install -d Ubuntu
echo   restart, open "Ubuntu" once to create a user, then re-run this command.
exit /b 1

:nodocker
echo.
echo   Docker isn't reachable from WSL ^(%DISTRO%^). Fix, once:
echo     1. Start Docker Desktop and wait until it says "Engine running".
echo     2. Docker Desktop ^> Settings ^> Resources ^> WSL integration ^> turn ON for "%DISTRO%" ^> Apply ^& restart.
echo   Then re-run this command.
exit /b 1
