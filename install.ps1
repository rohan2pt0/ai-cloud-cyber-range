# SecuRAX installer for Windows 10 and 11. Doc 75 has the details.
#
#   Invoke-WebRequest https://github.com/{{REPO_SLUG}}/releases/latest/download/install.ps1 -OutFile install.ps1
#   notepad install.ps1                       # read it first: it is short
#   powershell -ExecutionPolicy Bypass -File install.ps1            # rolling channel (main)
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Stable    # newest release
#
# SecuRAX runs inside WSL (Ubuntu on Windows). This script sizes WSL's memory from the PC (only when there is no .wslconfig),
# installs WSL and Ubuntu when missing (run as Administrator; one restart), then runs install.sh inside Ubuntu, which installs
# Docker Engine there (no Docker Desktop), turns HTTPS on, starts the estate and opens the Command Center.
param([switch]$Stable, [string]$Version = "")
$ErrorActionPreference = "Stop"

# A log of this run, and a window that never closes on an error before it can be read.
$LogDir = if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA "SecuRAX" } else { Join-Path $env:TEMP "SecuRAX" }
$Log = Join-Path $LogDir "last-run.log"
try { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null; "SecuRAX installer log. Started $(Get-Date -Format s)" | Set-Content -Path $Log -Encoding ascii } catch { $Log = $null }
function Note($t) { if ($Log) { try { Add-Content -Path $Log -Value $t -Encoding ascii } catch {} } }
function Stop-Here($why, $next, [int]$code = 1) {
  Write-Host ""
  Write-Host "  $why" -ForegroundColor Red
  Write-Host "  Next step:  $next" -ForegroundColor Yellow
  if ($Log) { Write-Host "  A log of this run:  $Log" }
  Note "FAILED: $why"; Note "Next step: $next"
  # started by a double-click or "Run with PowerShell": keep the window open until the person has read it
  if ([Environment]::UserInteractive -and -not [Console]::IsInputRedirected) { Read-Host "  Press Enter to close" | Out-Null }
  exit $code
}
trap { Stop-Here "The installer stopped: $($_.Exception.Message)" "copy this window's text into the chat, or run the same command again." }
$Repo = if ($env:SECURAX_REPO) { $env:SECURAX_REPO } else { "{{REPO_SLUG}}" }
if ($Repo -like "*{{*") {
  $brand = Join-Path $PSScriptRoot "brand.env"
  if (Test-Path $brand) { $Repo = ((Get-Content $brand | Where-Object { $_ -like "REPO_SLUG=*" }) -replace "^REPO_SLUG=", "") | Select-Object -First 1 }
  if (-not $Repo -or $Repo -like "*{{*") { Stop-Here "This copy of the installer does not know where SecuRAX lives (brand.env is not next to it)." "download install.ps1 from the Releases page, or run it from inside the SecuRAX folder." }
}

function Say($t) { Write-Host $t -ForegroundColor Cyan; Note $t }

$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# 1) Memory for WSL, sized from this PC (was a copy-paste step): only written when there is no .wslconfig yet
$wslcfg = Join-Path $env:USERPROFILE ".wslconfig"
if (-not (Test-Path $wslcfg)) {
  $gb   = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB)
  $mem  = if ($gb -ge 14) { 10 } elseif ($gb -ge 11) { 6 } else { 3 }
  $swap = if ($gb -ge 14) { 6 } else { 8 }
  "[wsl2]`nmemory=${mem}GB`nswap=${swap}GB`n" | Set-Content -Path $wslcfg -Encoding ascii
  Say "This PC has $gb GB: SecuRAX gets ${mem}GB, with ${swap}GB of swap (Windows keeps the rest)."
}

# 2) WSL and Ubuntu: installed for you when missing (one restart), then run this same command again
$env:WSL_UTF8 = "1"
$distro = $null
if (Get-Command wsl -ErrorAction SilentlyContinue) {
  # older Windows prints this list as UTF-16 whatever WSL_UTF8 says: drop the NUL characters before reading a name
  $distro = (wsl -l -q 2>$null) | ForEach-Object { ($_ -replace "`0", "").Trim() } | Where-Object { $_ -and $_ -notlike "docker-desktop*" } | Select-Object -First 1
}
# with no distribution, "wsl -l -q" prints a sentence, not a name: only trust a name that really starts
if ($distro) { wsl -d $distro -e true 2>$null | Out-Null; if ($LASTEXITCODE -ne 0) { Note "Not a working distribution: $distro"; $distro = $null } }
if (-not $distro) {
  if (-not $admin) { Stop-Here "Ubuntu (WSL) is needed, and installing it needs an Administrator window." "right-click Start, choose Terminal (Admin) or PowerShell (Admin), and run this same command again." }
  Say "Installing Ubuntu (WSL). Windows may ask to restart: do, then open Ubuntu once from the Start menu to pick a username,"
  Say "and run this same command again. It carries on from where it stopped."
  wsl --install -d Ubuntu
  exit 0
}
Say "SecuRAX installer: installing inside $distro (the fast WSL disk, not C:)"
$opt = if ($Version) { "--version $Version" } elseif ($Stable) { "--stable" } else { "" }
# install.sh from main: it has no version-specific logic, and main exists before the first release is tagged
$cmd = "cd ~ && curl -fsSLO https://raw.githubusercontent.com/$Repo/main/install.sh && SECURAX_REPO=$Repo bash install.sh $opt"
wsl -d $distro -e bash -lc $cmd
if ($LASTEXITCODE -ne 0) { Stop-Here "The install inside $distro stopped (code $LASTEXITCODE). The message above says why." "fix what it names and run this same command again: it carries on from where it stopped." $LASTEXITCODE }
Say ""
Say "Done. Docker Engine runs inside $distro (no Docker Desktop needed). Daily: open Ubuntu and type  securax up"
