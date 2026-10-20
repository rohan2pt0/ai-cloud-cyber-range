# SecuRAX first-response collector for Windows (doc 78). Windows PowerShell 5.1 or later.
# Run it FROM the responder USB in an ADMIN PowerShell on the affected machine:
#     powershell -ExecutionPolicy Bypass -File E:\SECURAX\collect.ps1        (E: is the USB; use its real letter)
#
# Order of volatility (RFC 3227): what disappears first is taken first.
#   1. memory, if tools\winpmem*.exe is on the USB
#   2. running state: time, sessions, processes (with path, command line, parent, hash), network connections with their
#      owning process, DNS cache, ARP, routes, shares, firewall and Defender status
#   3. persistence: Run keys, services, scheduled tasks, startup folders (listed with hashes instead of screenshots), WMI
#      subscriptions, and Autoruns if tools\autorunsc64.exe is on the USB
#   4. logs: Security, System, Application, PowerShell, Task Scheduler, RDP, Defender (and Sysmon if present), PowerShell histories
#   5. a full triage with KAPE (tools\KAPE\kape.exe) or a Velociraptor offline collector (tools\Collector*.exe), when present
# Then every file gets a SHA-256 in MANIFEST.sha256 and collector.json records who, when, where and with what.
# Everything is written to the USB only. Nothing is written to C:, nothing is changed or deleted on the machine.
#   -Quick   running state and persistence only (skips memory, event logs and full triage): for when minutes matter
param([switch]$Quick)
$ErrorActionPreference = "Continue"
$Here = $PSScriptRoot
$Case = if (Test-Path "$Here\CASE_ID") { (Get-Content "$Here\CASE_ID" -Raw).Trim() } else { "NO-CASE" }
$HostName = $env:COMPUTERNAME
$Stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$Out = Join-Path $Here "evidence\$HostName-$Stamp"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$Log = Join-Path $Out "collector.log"
function Say($t) { Write-Host $t; Add-Content -Path $Log -Value ("{0} {1}" -f [DateTime]::UtcNow.ToString("o"), $t) }
function Run($name, [scriptblock]$block) {
  try { & $block *> (Join-Path $Out "$name.txt"); Say "  ok  $name" } catch { Say "  !!  $name : $($_.Exception.Message)" }
}
function Csv($name, [scriptblock]$block) {
  try { & $block | Export-Csv -NoTypeInformation -Encoding UTF8 -Path (Join-Path $Out "$name.csv"); Say "  ok  $name.csv" } catch { Say "  !!  $name : $($_.Exception.Message)" }
}
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Say "!! Not running as Administrator: some items will be incomplete. Right-click PowerShell > Run as administrator, then run this again." }
Say "SecuRAX collector · case $Case · host $HostName · started $([DateTime]::UtcNow.ToString('o'))"
Say "Writing to $Out"

# 1. memory first
$pmem = Get-ChildItem -Path "$Here\tools" -Filter "winpmem*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($Quick) { Say "  --  memory (quick mode)" }
elseif ($pmem) { Say "Capturing memory with $($pmem.Name) (can take a while; do not remove the USB)..."; & $pmem.FullName (Join-Path $Out "memory.raw") *>> $Log; Say "  ok  memory.raw (check collector.log)" }
else { Say "  --  memory (put winpmem_mini_x64.exe in tools\ on the USB, or use FTK Imager / Magnet RAM Capture by hand)" }

# 2. running state
Run "time" { "UTC   " + [DateTime]::UtcNow.ToString("o"); "Local " + (Get-Date).ToString("o"); "TZ    " + (Get-TimeZone).Id }
Run "systeminfo" { systeminfo }
Run "sessions" { query user; "`n== net session"; net session }
Run "netstat-ano" { netstat -ano }
Csv "connections-with-process" { Get-NetTCPConnection | ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
  [pscustomobject]@{Local="$($_.LocalAddress):$($_.LocalPort)"; Remote="$($_.RemoteAddress):$($_.RemotePort)"; State=$_.State; PID=$_.OwningProcess; Process=$p.ProcessName; Path=$p.Path} } }
Run "dns-cache" { ipconfig /displaydns }
Run "ipconfig" { ipconfig /all }
Run "arp" { arp -a }
Run "routes" { route print }
Run "tasklist" { tasklist /v; "`n== services per process"; tasklist /svc }
$procs = Get-CimInstance Win32_Process
Csv "processes" { $procs | Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine, CreationDate }
Csv "process-binary-hashes" { $procs.ExecutablePath | Where-Object { $_ } | Sort-Object -Unique | ForEach-Object { Get-FileHash -Algorithm SHA256 -Path $_ -ErrorAction SilentlyContinue } }
Run "shares" { net share }
Run "local-admins" { net localgroup administrators; "`n== users"; net user }
Run "firewall" { netsh advfirewall show allprofiles }
Run "defender" { Get-MpComputerStatus | Format-List *; "`n== threats"; Get-MpThreatDetection | Format-List * }
Copy-Item "$env:WINDIR\System32\drivers\etc\hosts" (Join-Path $Out "hosts.txt") -ErrorAction SilentlyContinue

# 3. persistence
Csv "services" { Get-CimInstance Win32_Service | Select-Object Name, DisplayName, State, StartMode, PathName, StartName }
Run "scheduled-tasks" { schtasks /query /fo csv /v }
foreach ($k in "HKLM\Software\Microsoft\Windows\CurrentVersion\Run","HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce","HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run","HKCU\Software\Microsoft\Windows\CurrentVersion\Run","HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce") {
  $f = Join-Path $Out ("reg-" + ($k -replace '[\\: ]', '_') + ".reg"); reg export $k $f /y *> $null
}
Say "  ok  run-keys (reg-*.reg)"
$startup = @("$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Startup") + (Get-ChildItem "$env:SystemDrive\Users" -Directory -ErrorAction SilentlyContinue | ForEach-Object { "$($_.FullName)\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup" })
Csv "startup-folders" { foreach ($d in $startup) { if (Test-Path $d) { Get-ChildItem -Force -Path $d -ErrorAction SilentlyContinue | ForEach-Object {
  [pscustomobject]@{Folder=$d; Name=$_.Name; Size=$_.Length; Created=$_.CreationTimeUtc; Modified=$_.LastWriteTimeUtc; SHA256=(Get-FileHash -Algorithm SHA256 $_.FullName -ErrorAction SilentlyContinue).Hash} } } } }
Run "wmi-subscriptions" { Get-CimInstance -Namespace root/subscription -ClassName __EventFilter | Format-List *; Get-CimInstance -Namespace root/subscription -ClassName CommandLineEventConsumer | Format-List *; Get-CimInstance -Namespace root/subscription -ClassName __FilterToConsumerBinding | Format-List * }
$ar = Get-ChildItem -Path "$Here\tools" -Filter "autorunsc64.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ar) { $ar = Get-ChildItem -Path "$Here\tools" -Filter "autorunsc.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 }
if ($ar) { & $ar.FullName -accepteula -nobanner -a * -c -h -s "*" > (Join-Path $Out "autoruns.csv") 2>> $Log; Say "  ok  autoruns.csv" }
else { Say "  --  autoruns (put autorunsc64.exe from Sysinternals in tools\ on the USB)" }

# 4. logs (exported, never cleared) and PowerShell histories
if (-not $Quick) {
New-Item -ItemType Directory -Force -Path (Join-Path $Out "eventlogs") | Out-Null
foreach ($ch in "Security","System","Application","Microsoft-Windows-PowerShell/Operational","Microsoft-Windows-TaskScheduler/Operational","Microsoft-Windows-TerminalServices-LocalSessionManager/Operational","Microsoft-Windows-Windows Defender/Operational","Microsoft-Windows-Sysmon/Operational") {
  $f = Join-Path $Out ("eventlogs\" + ($ch -replace '[/ ]', '_') + ".evtx"); wevtutil epl "$ch" "$f" *> $null
}
Say "  ok  eventlogs"
}
Get-ChildItem "$env:SystemDrive\Users" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
  $h = "$($_.FullName)\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"
  if (Test-Path $h) { Copy-Item $h (Join-Path $Out "pshistory-$($_.Name).txt") -ErrorAction SilentlyContinue }
}
Say "  ok  powershell-histories"

# 5. full triage, when the tool is on the USB
$kape = "$Here\tools\KAPE\kape.exe"
if ($Quick) { Say "  --  full triage (quick mode)" }
elseif (Test-Path $kape) {
  Say "Running KAPE (SANS triage; can take 10-60 minutes)..."
  & $kape --tsource "$env:SystemDrive" --tdest (Join-Path $Out "kape") --target "!SANS_Triage" --vss --zip $HostName *>> $Log
  Say "  ok  kape (check collector.log)"
} else {
  $vr = Get-ChildItem -Path "$Here\tools" -Filter "Collector*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($vr) { Say "Running the Velociraptor offline collector..."; Push-Location $Out; & $vr.FullName *>> $Log; Pop-Location; Say "  ok  velociraptor (its zip is in this folder)" }
  else { Say "  --  full triage (put a Velociraptor offline collector or, if you hold a licence, KAPE in tools\)" }
}

# seal: a hash for every file. Nothing is written to the folder after this except collector.json
Say "Sealing: hashing every file"
$lines = Get-ChildItem -Path $Out -Recurse -File | Where-Object { $_.Name -notin @("MANIFEST.sha256", "collector.json") } | ForEach-Object {
  $rel = "./" + $_.FullName.Substring($Out.Length + 1).Replace("\", "/")
  "{0}  {1}" -f (Get-FileHash -Algorithm SHA256 $_.FullName).Hash.ToLower(), $rel
}
[IO.File]::WriteAllLines((Join-Path $Out "MANIFEST.sha256"), [string[]]$lines)
$man = (Get-FileHash -Algorithm SHA256 (Join-Path $Out "MANIFEST.sha256")).Hash.ToLower()
@{case=$Case; host=$HostName; os=(Get-CimInstance Win32_OperatingSystem).Caption; collected_by="$env:USERDOMAIN\$env:USERNAME"; started_utc=$Stamp;
  finished_utc=[DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ"); collector="securax collect.ps1"; manifest_sha256=$man} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $Out "collector.json")
Write-Host "Done. Files: $($lines.Count) · folder: $Out"
Write-Host "Next: write the time and your name on the custody form, safely eject the USB, and do NOT switch this machine off."
