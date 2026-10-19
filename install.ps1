# SecuRAX installer for Windows 10 and 11. Doc 75 has the details.
#
#   Invoke-WebRequest https://github.com/{{REPO_SLUG}}/releases/latest/download/install.ps1 -OutFile install.ps1
#   notepad install.ps1                       # read it first: it is short
#   powershell -ExecutionPolicy Bypass -File install.ps1            # rolling channel (main)
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Stable    # newest release
#
# SecuRAX runs inside WSL (Ubuntu on Windows), like most Linux server software on a Windows PC. This script checks that
# WSL and Ubuntu are there (and tells you the one command if not), then runs install.sh inside Ubuntu. It changes nothing
# on Windows itself.
param([switch]$Stable, [string]$Version = "")
$ErrorActionPreference = "Stop"
$Repo = if ($env:SECURAX_REPO) { $env:SECURAX_REPO } else { "{{REPO_SLUG}}" }
if ($Repo -like "*{{*") {
  $brand = Join-Path $PSScriptRoot "brand.env"
  if (Test-Path $brand) { $Repo = ((Get-Content $brand | Where-Object { $_ -like "REPO_SLUG=*" }) -replace "^REPO_SLUG=", "") | Select-Object -First 1 }
  if (-not $Repo -or $Repo -like "*{{*") { Write-Host "Which repository? Set it first:  `$env:SECURAX_REPO='owner/repo'" -ForegroundColor Red; exit 1 }
}

function Say($t) { Write-Host $t -ForegroundColor Cyan }

if (-not (Get-Command wsl -ErrorAction SilentlyContinue)) {
  Say "WSL is not available on this Windows. Open PowerShell as Administrator, run:  wsl --install -d Ubuntu"
  Say "Restart when it asks, open Ubuntu once to make a user, then run this installer again."
  exit 1
}
$env:WSL_UTF8 = "1"
$distro = (wsl -l -q 2>$null) | ForEach-Object { $_.Trim() } | Where-Object { $_ -and $_ -notlike "docker-desktop*" } | Select-Object -First 1
if (-not $distro) {
  Say "WSL is there but no Linux is installed. Open PowerShell as Administrator, run:  wsl --install -d Ubuntu"
  Say "Then open Ubuntu once from the Start menu to make a user, and run this installer again."
  exit 1
}
Say "SecuRAX installer: installing inside $distro (the fast WSL disk, not C:)"
$opt = if ($Version) { "--version $Version" } elseif ($Stable) { "--stable" } else { "" }
# install.sh from main: it has no version-specific logic, and main exists before the first release is tagged
$cmd = "cd ~ && curl -fsSLO https://raw.githubusercontent.com/$Repo/main/install.sh && SECURAX_REPO=$Repo bash install.sh $opt"
wsl -d $distro -e bash -lc $cmd
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Say ""
Say "Docker: install Docker Desktop, then Settings > Resources > WSL integration > turn on $distro."
Say "Then start everything from here with:  wsl -d $distro --cd ~/securax ./securax up"
