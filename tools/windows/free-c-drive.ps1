<#
  Free the C: drive that Docker Desktop, WSL and local AI models fill (doc 80, section "Windows: the C: drive").

  Run it in Windows PowerShell (not in Ubuntu):
      powershell -ExecutionPolicy Bypass -File .\tools\windows\free-c-drive.ps1          # report only: changes nothing
      powershell -ExecutionPolicy Bypass -File .\tools\windows\free-c-drive.ps1 -Fix     # asks before each step
  Compacting virtual disks needs an Administrator PowerShell; the script says when.

  Why C: fills: Docker's and Ubuntu's Linux disks are .vhdx files under your user folder on C:. They grow as images and
  data arrive and never shrink by themselves, even after you delete things inside. Local AI models (Ollama) also live on C:.
  A full C: drive breaks Windows updates and can make WSL fail to mount drives or crash programs.

  What it never does: delete your files, Docker volumes (your estate's data), or a disk image. Every step is reversible
  or only removes caches Docker rebuilds by itself.
#>
param([switch]$Fix, [string]$Target = "")

$ErrorActionPreference = "Continue"
function GB($b) { "{0:N1} GB" -f ($b / 1GB) }
function Ask($q) { if (-not $Fix) { return $false }; $a = Read-Host "$q [y/N]"; return $a -match '^(y|yes)$' }
function Free($d) { (Get-PSDrive -Name $d.TrimEnd(':') -ErrorAction SilentlyContinue).Free }
function Size($p) { if (Test-Path $p) { (Get-ChildItem $p -Recurse -Force -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum } else { 0 } }
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# The drive to move things to: the one with the most free space that is not C:.
if (-not $Target) {
  $best = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name -ne 'C' -and $_.Free -gt 20GB } | Sort-Object Free -Descending | Select-Object -First 1
  if ($best) { $Target = "$($best.Name):" }
}

Write-Host "`nC: has $(GB (Free 'C')) free." -ForegroundColor Cyan
if ($Target) { Write-Host "Best place to move things: $Target ($(GB (Free $Target)) free)." } else { Write-Host "No other drive with 20 GB free was found." }

# ── What is using the space ──────────────────────────────────────────────────────────────────────────────────────────
$disks = @()
$disks += Get-ChildItem "$env:LOCALAPPDATA\Docker" -Recurse -Filter *.vhdx -ErrorAction SilentlyContinue | ForEach-Object { [pscustomobject]@{ What = "Docker Desktop disk"; Path = $_.FullName; Bytes = $_.Length } }
Get-ChildItem "HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss" -ErrorAction SilentlyContinue | ForEach-Object {
  $p = Get-ItemProperty $_.PSPath
  if (-not $p.BasePath) { return }
  $v = Join-Path ($p.BasePath -replace '^\\\\\?\\', '') "ext4.vhdx"           # newer WSL writes \\?\C:\... ; the C: check needs a plain path
  if ($p.DistributionName -and (Test-Path $v) -and -not ($disks | Where-Object { $_.Path -eq $v })) {
    $disks += [pscustomobject]@{ What = "WSL: $($p.DistributionName)"; Path = $v; Bytes = (Get-Item $v).Length } }
}
$ollama = if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { "$env:USERPROFILE\.ollama\models" }
$rows = @($disks) + @(
  [pscustomobject]@{ What = "Ollama models (Windows)"; Path = $ollama; Bytes = (Size $ollama) },
  [pscustomobject]@{ What = "Your temp folder"; Path = $env:TEMP; Bytes = (Size $env:TEMP) },
  [pscustomobject]@{ What = "Downloads"; Path = "$env:USERPROFILE\Downloads"; Bytes = (Size "$env:USERPROFILE\Downloads") }
)
Write-Host "`nThe biggest users of C: that SecuRAX knows about:"
$rows | Where-Object { $_.Bytes -gt 0 -and $_.Path -like 'C:*' } | Sort-Object Bytes -Descending | ForEach-Object { "  {0,-28} {1,10}   {2}" -f $_.What, (GB $_.Bytes), $_.Path }

if (-not $Fix) {
  Write-Host "`nNothing was changed. To free space, run again with -Fix (it asks before each step)." -ForegroundColor Yellow
  Write-Host "The quickest win is usually step 4: move Docker's disk to $Target in Docker Desktop's settings."
  return
}

# ── 1. Caches that are safe to clear ──────────────────────────────────────────────────────────────────────────────────
if (Ask "1. Clear temp files older than 7 days?") {
  Get-ChildItem $env:TEMP -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer -and $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item -Force -ErrorAction SilentlyContinue
  Write-Host "   done. C: now has $(GB (Free 'C')) free."
}
if ((Get-Command docker -ErrorAction SilentlyContinue) -and (Ask "2. Remove Docker build cache and unused, untagged image layers? (your containers, images in use and volumes are kept)")) {
  docker builder prune -f | Select-Object -Last 1
  docker image prune -f | Select-Object -Last 1
  Write-Host "   done. This frees space INSIDE Docker's disk; step 4 or 5 returns it to C:."
}

# ── 3. Local AI models to another drive ───────────────────────────────────────────────────────────────────────────────
if ($Target -and (Test-Path $ollama) -and $ollama -like 'C:*' -and (Ask "3. Move Ollama models to $Target\ollama\models (Ollama is stopped first, then pointed there)?")) {
  Get-Process ollama* -ErrorAction SilentlyContinue | Stop-Process -Force
  $dest = "$Target\ollama\models"; New-Item -ItemType Directory -Force -Path $dest | Out-Null
  robocopy $ollama $dest /E /MOVE /R:1 /W:1 /NFL /NDL /NJH | Out-Null
  [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $dest, "User")
  Write-Host "   done. Start Ollama again from the Start menu; 'ollama list' should show the same models."
}

# ── 4. Docker's disk to another drive (Docker moves it for you) ───────────────────────────────────────────────────────
Write-Host "`n4. Move Docker's disk off C: (the biggest win, and Docker does it safely):"
Write-Host "   Docker Desktop -> Settings -> Resources -> Advanced -> Disk image location -> Browse -> $Target\DockerDesktop -> Apply & restart."
Write-Host "   Your containers, images and volumes move with it."

# ── 5. Compact the Linux disks (they never shrink by themselves) ──────────────────────────────────────────────────────
if ($disks.Count -and (Ask "5. Shut WSL and Docker down and compact the Linux disks? (quit Docker Desktop first; needs Administrator)")) {
  if (-not $admin) { Write-Host "   Skipped: open PowerShell as Administrator and run this script with -Fix again." -ForegroundColor Yellow }
  else {
    wsl --shutdown; Start-Sleep 5
    foreach ($d in $disks) {
      $before = (Get-Item $d.Path).Length
      if (Get-Command Optimize-VHD -ErrorAction SilentlyContinue) { Optimize-VHD -Path $d.Path -Mode Full }
      else {
        $script = "select vdisk file=`"$($d.Path)`"`nattach vdisk readonly`ncompact vdisk`ndetach vdisk`n"
        $tmp = New-TemporaryFile; Set-Content $tmp $script -Encoding ascii; diskpart /s $tmp | Out-Null; Remove-Item $tmp
      }
      Write-Host ("   {0}: {1} -> {2}" -f $d.What, (GB $before), (GB (Get-Item $d.Path).Length))
    }
  }
}

# ── 6. Move the Ubuntu disk itself ────────────────────────────────────────────────────────────────────────────────────
$ub = $disks | Where-Object { $_.What -like 'WSL:*' -and $_.What -notlike '*docker-desktop*' -and $_.Path -like 'C:*' } | Select-Object -First 1   # Docker's own disks move in step 4
if ($Target -and $ub -and (Ask "6. Move $($ub.What) to $Target\WSL? (WSL is shut down first; back up anything important before)")) {
  $name = $ub.What.Substring(5); wsl --shutdown
  wsl --manage $name --move "$Target\WSL\$name"
  if ($LASTEXITCODE -ne 0) { Write-Host "   Your WSL is too old for --move. Run 'wsl --update' first, then this step again." -ForegroundColor Yellow }
  else { Write-Host "   done. Open Ubuntu once to check it starts." }
}

Write-Host "`nC: now has $(GB (Free 'C')) free." -ForegroundColor Cyan
