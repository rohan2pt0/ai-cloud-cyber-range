# Give the estate a home on a drive with room (off C:)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** A guide + a guard for the Windows/WSL single point of failure: WSL and Docker default to C:, which fills and takes the estate down. ./securax doctor now shows free space per Windows drive and, when the estate's disk is low, names the roomiest drive and points here; the one-time move (wsl --manage --move or export/import, plus Docker Desktop's disk image location) relocates WSL + Docker + SecuRAX to a roomy drive, and backups go to a separate drive so no one disk is a single point of failure. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The single point of failure this removes:** on Windows, WSL2 keeps your whole Linux disk as one file
(`ext4.vhdx`) on **C:** by default, and Docker Desktop stores its images and volumes on C: too. SecuRAX
lives *inside* WSL, so **when C: fills, Docker dies and the whole estate goes down.** Moving WSL + Docker
to a roomier drive (say **D:**) fixes it once; the estate moves with WSL. `./securax doctor` now warns
when your disk is low and names the roomiest drive.

SecuRAX can't do this from *inside* WSL (it can't move its own Windows drive). Run these **in Windows
PowerShell**, and back up first.

## 1. See what you have

```powershell
wsl -l -v                               # your distros and their WSL version
Get-PSDrive -PSProvider FileSystem      # free space per drive — pick the roomiest (e.g. D:)
```

## 2. Move the WSL distro (quit Docker Desktop FIRST, or the move is blocked)

The move needs the distro's disk file to be fully released. `wsl --shutdown` alone is **not enough**: Docker Desktop
restarts the WSL backend within seconds and re-mounts the disk, so `--move` keeps failing with
`WSL_E_DISTRO_NOT_STOPPED` / "the VHD is currently in use" no matter how many times you run `wsl --shutdown`. The tell is
`wsl -l -v` still showing `docker-desktop  Running`.

So, in this order:

```powershell
# 1) Quit Docker Desktop: tray icon → Quit Docker Desktop.
#    Settings → General → uncheck "Start Docker Desktop when you sign in".
# 2) Stop its Windows service so it can't auto-restart (run PowerShell as Administrator):
net stop com.docker.service
#    Also close any VS Code window attached to WSL and any open Ubuntu terminal — they pin the disk too.
# 3) Now stop WSL and CONFIRM everything is Stopped:
wsl --shutdown
Start-Sleep 10
wsl -l -v            # every distro, especially docker-desktop, must read "Stopped" before you go on
```

**Easiest (Windows 11 / recent WSL) — one step, moves the disk and updates the registry:**
```powershell
wsl --manage <Distro> --move D:\wsl\<Distro>
```
If it *still* says "VHD is currently in use", a process is holding it — `docker-desktop` is up again (re-do step 2), or a
VS Code / terminal is attached. When nothing can be stopped, the export/import path below is immune to this.

**If `--manage --move` isn't available, export/import (works on any WSL2):**
```powershell
mkdir D:\wsl\<Distro>
wsl --export <Distro> D:\wsl\<Distro>.vhdx --vhd      # this file IS your backup — keep it
wsl --unregister <Distro>
wsl --import <Distro> D:\wsl\<Distro> D:\wsl\<Distro>.vhdx --vhd --version 2
<Distro> config --default-user <you>                 # re-import resets to root; set your user back
```

Keep the exported `.vhdx` until you've confirmed the distro boots (`wsl -d <Distro>`) and SecuRAX is
intact (`./securax status`). Only then delete the backup.

## 3. Move Docker's data too (or it stays on C:)

Docker Desktop → **Settings → Resources → Advanced → Disk image location → `D:\DockerData`** → Apply &
Restart. Docker keeps two hidden distros (`docker-desktop`, `docker-desktop-data`); confirm neither is
left on C: with `wsl -l -v`.

**If after all the `wsl --shutdown`s a command inside WSL can't reach the internet** (e.g. `./securax update` says
`Could not resolve host: github.com`): that is **WSL DNS**, not the site being down — the shutdown/restart often leaves
`/etc/resolv.conf` pointing at a nameserver that no longer answers. Inside Ubuntu, test with `getent hosts github.com`;
if it fails, pin a working resolver:
```bash
printf '[network]\ngenerateResolvConf = false\n' | sudo tee /etc/wsl.conf
sudo rm -f /etc/resolv.conf
printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' | sudo tee /etc/resolv.conf
```
then `wsl --shutdown` once more and reopen. (A VPN or corporate DNS can cause the same; so can Docker Desktop still
starting up.)

## 4. The real antifragility: don't depend on one drive

One roomy drive beats a full C:, but *one* drive is still a single point of failure. Keep SecuRAX's
**backups on a different drive** than the live estate, so a drive filling — or dying — can't take both:

```bash
./securax backup            # point its target at the other drive or an external disk
```

Live estate on D:, backups on a separate disk. That is the estate's own rule — no new single point of
failure — applied to your hardware.

## Reminder

- `./securax doctor` shows free space per Windows drive and flags when the estate's disk is low.
- `./securax storage` shows what's growing and what's safe to clean before you even need to move.
