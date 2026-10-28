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

## 2. Move the WSL distro (shut everything down first)

```powershell
wsl --shutdown
```

**Easiest (Windows 11 / recent WSL) — one step, moves the disk and updates the registry:**
```powershell
wsl --manage <Distro> --move D:\wsl\<Distro>
```

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
