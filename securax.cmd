@echo off
REM SecuRAX on Windows:  .\securax.cmd up | down | update | doctor | providers add | verify ...
REM `securax` is a bash script, so this runs it inside WSL (Ubuntu): the supported way on Windows.
REM Every double-click launcher (*-Windows.bat) goes through this file. It says each step in plain words,
REM writes %LOCALAPPDATA%\SecuRAX\last-run.log, and on a failure prints the one next step and returns 1.
REM It never pauses (it is also used from PowerShell); the .bat files pause.
REM Rules for editing (lifecycle/tests/test_windows_launchers.py holds them): ASCII only, CRLF endings,
REM never parse "wsl -l" (its output is UTF-16 on older Windows), no %* inside a ( ) block.
setlocal EnableExtensions DisableDelayedExpansion
set "HERE=%~dp0"
set "RC=1"
set "PUSHED="

REM ---- the log: one file, replaced on every run -------------------------------------------------------
set "LOGDIR=%LOCALAPPDATA%\SecuRAX"
if not defined LOCALAPPDATA set "LOGDIR=%TEMP%\SecuRAX"
if not exist "%LOGDIR%\" mkdir "%LOGDIR%" >nul 2>&1
set "LOG=%LOGDIR%\last-run.log"
2>nul (echo SecuRAX launcher log. Started %DATE% %TIME%)>"%LOG%" || set "LOG=nul"
2>nul (echo Launcher folder: "%HERE%")>>"%LOG%"
2>nul >>"%LOG%" echo Command: securax %*
2>nul (ver)>>"%LOG%"

REM ---- step 1: WSL and a Linux distribution ----------------------------------------------------------
echo   [1/4] Looking for Linux on Windows (WSL)...
where wsl >nul 2>&1
if errorlevel 1 goto nowsl
set "DISTRO="
REM Ask the default distribution for its own name. Linux prints plain text; "wsl -l" does not.
wsl -e true >nul 2>&1
if errorlevel 1 goto trynamed
for /f "usebackq delims=" %%d in (`wsl -e sh -c "echo $WSL_DISTRO_NAME" 2^>nul`) do if not defined DISTRO set "DISTRO=%%d"
REM Docker Desktop's own distribution is not a place to run SecuRAX.
if defined DISTRO if /i "%DISTRO:~0,14%"=="docker-desktop" set "DISTRO="
:trynamed
if defined DISTRO goto havedistro
for %%n in (Ubuntu Ubuntu-24.04 Ubuntu-22.04 Ubuntu-20.04 Debian) do if not defined DISTRO wsl -d %%n -e true >nul 2>&1 && set "DISTRO=%%n"
if not defined DISTRO goto nowsl
:havedistro
echo         Found: %DISTRO%
2>nul (echo Step 1 ok. Distribution: %DISTRO%)>>"%LOG%"

REM ---- step 2: where the SecuRAX files are -----------------------------------------------------------
echo   [2/4] Finding the SecuRAX files...
REM Prefer the FAST copy inside WSL (~/securax, made by install.ps1 or wsl-setup.sh) over this Windows folder.
set "WORK="
for /f "usebackq delims=" %%h in (`wsl -d "%DISTRO%" -e sh -c "test -f ~/securax/securax && cd ~/securax && pwd" 2^>nul`) do if not defined WORK set "WORK=%%h"
if defined WORK goto havework
if not exist "%HERE%securax" goto nofiles
pushd "%HERE%" >nul 2>&1
if errorlevel 1 goto nofiles
set "PUSHED=1"
wsl -d "%DISTRO%" -e test -f ./securax >nul 2>&1
if errorlevel 1 goto nofiles
REM Strip any Windows line endings that would break the bash script (an old checkout).
wsl -d "%DISTRO%" -e sed -i "s/\r$//" securax >nul 2>&1
echo         Using this Windows folder. It works, but it is slower than a copy inside %DISTRO%.
2>nul (echo Step 2 ok. Using the Windows folder.)>>"%LOG%"
goto docker
:havework
echo         Using the fast copy inside %DISTRO%: %WORK%
2>nul (echo Step 2 ok. Using "%WORK%" inside %DISTRO%.)>>"%LOG%"

REM ---- step 3: Docker --------------------------------------------------------------------------------
:docker
echo   [3/4] Checking Docker...
set "TRIES=0"
set "ENGINE="
wsl -d "%DISTRO%" -e docker info >nul 2>&1
if not errorlevel 1 goto dockerok
REM Docker Engine installed inside the distribution (the install.ps1 way) may only be stopped: start it.
wsl -d "%DISTRO%" -e sh -c "command -v dockerd" >nul 2>&1
if errorlevel 1 goto dockerbad
set "ENGINE=1"
echo         Docker is stopped. Starting it...
wsl -d "%DISTRO%" -u root -e sh -c "systemctl start docker || service docker start" >nul 2>&1
:dockerwait
wsl -d "%DISTRO%" -e docker info >nul 2>&1
if not errorlevel 1 goto dockerok
set /a TRIES+=1
if %TRIES% GEQ 8 goto dockerbad
ping -n 3 127.0.0.1 >nul 2>&1
goto dockerwait
:dockerbad
REM These commands explain a problem themselves, so they run even when Docker is down.
set "CANRUN="
if "%~1"=="" set "CANRUN=1"
for %%c in (why doctor help version) do if /i "%~1"=="%%c" set "CANRUN=1"
if not defined CANRUN goto nodocker
echo         Docker is not running. Carrying on, because this command can explain it.
2>nul (echo Step 3: Docker not reachable. Carrying on for this command.)>>"%LOG%"
goto run
:dockerok
echo         Docker is running.
2>nul (echo Step 3 ok. Docker is running.)>>"%LOG%"

REM ---- step 4: run it --------------------------------------------------------------------------------
:run
echo   [4/4] Running:  securax %*
echo.
if defined WORK goto runwork
wsl -d "%DISTRO%" -e bash ./securax %*
set "RC=%errorlevel%"
goto ran
:runwork
wsl -d "%DISTRO%" --cd "%WORK%" -e bash ./securax %*
set "RC=%errorlevel%"
:ran
2>nul (echo Step 4: securax ended with exit code %RC%. %DATE% %TIME%)>>"%LOG%"
if "%RC%"=="0" goto end
echo.
echo   SecuRAX stopped with a problem (code %RC%). The message above says why.
echo   Next step:  double-click WHATS-WRONG-Windows.bat   (or run  .\securax.cmd why)
echo   A log of this run:  %LOG%
goto end

:nowsl
echo.
echo   SecuRAX needs WSL with Ubuntu (Linux on Windows), and it is not ready on this PC.
echo   Next step, once:  right-click Start, choose "Terminal (Admin)" or "PowerShell (Admin)", and run
echo       wsl --install -d Ubuntu
echo   Restart the PC, open "Ubuntu" from the Start menu once to pick a username, then try again.
echo   A log of this run:  %LOG%
2>nul (echo FAILED at step 1: no working WSL distribution.)>>"%LOG%"
2>nul (wsl --status)>>"%LOG%"
goto end

:nofiles
echo.
echo   The SecuRAX files are not next to this launcher:
echo       "%HERE%"
echo   Next step:  keep the whole SecuRAX folder together. If you opened it from a ZIP, right-click the ZIP,
echo   choose "Extract All", open the extracted folder and start again from there.
echo   A log of this run:  %LOG%
2>nul (echo FAILED at step 2: no securax script next to the launcher, and no ~/securax inside %DISTRO%.)>>"%LOG%"
goto end

:nodocker
echo.
echo   Docker is not reachable from %DISTRO%, so SecuRAX cannot start its services.
if defined ENGINE goto nodockerengine
echo   Next step:  start Docker Desktop and wait until it says "Engine running". If it already does, open
echo   Docker Desktop, Settings, Resources, WSL integration, turn it ON for "%DISTRO%", press Apply, then try again.
echo   No Docker at all? In PowerShell run:  powershell -ExecutionPolicy Bypass -File install.ps1
goto nodockerlog
:nodockerengine
echo   Next step:  open "%DISTRO%" from the Start menu and run:   sudo service docker start
echo   Then try again. If that prints an error, copy it into the chat.
:nodockerlog
echo   A log of this run:  %LOG%
2>nul (echo FAILED at step 3: docker info does not answer inside %DISTRO%. Engine inside WSL: "%ENGINE%")>>"%LOG%"
goto end

:end
if defined PUSHED popd
endlocal & exit /b %RC%
