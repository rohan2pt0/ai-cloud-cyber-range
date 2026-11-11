# SecuRAX on Windows — one command (about 10 minutes, mostly downloads)

One command does the setup. If it says **STOP**, do what it says, then run the same command again: it is safe to repeat.

## Step 1 — one command (PowerShell as Administrator)
Right-click **Start → Terminal (Admin)**, paste, press Enter. The script is saved to a file first, so you can read it (`notepad install.ps1`):
```powershell
Invoke-WebRequest https://raw.githubusercontent.com/rohan2pt0/ai-cloud-cyber-range/main/install.ps1 -OutFile install.ps1
powershell -ExecutionPolicy Bypass -File install.ps1
```
It sizes SecuRAX's memory from your PC, installs Ubuntu (WSL) if it is missing, and then, inside Ubuntu, installs Docker Engine
(it asks for your Ubuntu password once), turns HTTPS on, starts the estate and opens your Command Center. No Docker Desktop, no settings to click.

If Windows installs Ubuntu first, it asks to restart: restart, open **Ubuntu** once from the Start menu to pick a username and
password, then run the same two lines again. It carries on from where it stopped.

## Step 2 (optional, any time) — free AI keys and the rest
Everything works on the private local model. For faster answers, and for phones and backups, one step at a time:
```bash
securax finish
```

## Use it
Your Command Center opens in the browser by itself (or run `./securax open`, which prints the right address: `http://localhost:8088/hub.html`, or `https://hub.securax.localhost/hub.html` once HTTPS is on). Everything is linked from there.

## Installed before 11 November 2026? Turn HTTPS on once
A new install is on HTTPS already. An older one: first export your Life OS data (**Ops → System health → Export backup**: the
secure address starts empty), then in Ubuntu run `cd ~/securax && ./securax tls on && ./securax tls trust --apply && ./securax down && ./securax up`,
open **https://hub.securax.localhost/hub.html** and import the backup there. Details: `docs/securax/40-ENCRYPTION-IN-TRANSIT.md`.

## Every day after that
Open **Ubuntu**, then:
| I want to… | Type |
|---|---|
| start | `cd ~/securax && ./securax up` |
| stop (free RAM) | `cd ~/securax && ./securax down` |
| update to the latest | `cd ~/securax && ./securax update` |
| something is wrong | `cd ~/securax && ./securax doctor` |
| add / change an API key | `cd ~/securax && ./securax keys` |

Or from PowerShell, in the old Windows folder, the same commands work as `.\securax.cmd up` (it automatically uses the fast Ubuntu copy once Step 1 is done).

## If something fails
Copy **everything** the window printed and paste it to me. Don't try to fix it yourself.

## Something not working? Two double-clicks (no commands, no folders)
In the SecuRAX folder (where you unzipped or cloned it) double-click:
- **`WHATS-WRONG-Windows.bat`** (runs `./securax why`): shows what is running, what stopped and why, in plain words. If it is still unclear, copy the window's text into the chat.
- **`UPDATE-Windows.bat`** (runs `./securax update`): gets the latest version safely (backs up first, goes back if the new version does not start).

In Ubuntu you can also type `securax why`, `securax update`, `securax status` from **any folder** (`./securax shortcut` sets this up once; the installer already did it. Undo: `./securax shortcut off`). "No such file or directory" means you were in the wrong folder: this removes that problem.
