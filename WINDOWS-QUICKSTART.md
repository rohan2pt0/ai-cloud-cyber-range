# SecuRAX on Windows — follow these steps in order (about 15 minutes, once)

Everything below is copy-paste. Don't skip a step. If a step prints a message that says **STOP**, do what it says, then paste that step again.

## Step 1 — give SecuRAX enough memory (PowerShell, as Administrator)
Right-click **Start → Terminal (Admin)** (or "Windows PowerShell (Admin)"), paste, press Enter:
```powershell
@"
[wsl2]
memory=10GB
swap=6GB
"@ | Set-Content -Path "$env:USERPROFILE\.wslconfig" -Encoding ascii
wsl --shutdown
```
(This reserves 10 GB of your 16 GB for Docker; Windows keeps 6 GB. If you ever have other heavy apps open, lower it to `8GB`.)

## Step 2 — start Docker Desktop and switch on the Ubuntu link
1. Start menu → **Docker Desktop**. Wait until the bottom-left says **Engine running**.
2. Gear icon (Settings) → **Resources** → **WSL integration** → turn **ON** the switch next to **Ubuntu** → **Apply & restart**.

## Step 3 — install SecuRAX (inside Ubuntu)
1. Start menu → type **Ubuntu** → open it (a black window; first time it asks you to create a username/password — pick anything simple, and remember it).
2. Paste these two lines and press Enter (Ubuntu may ask for your password once; typing is invisible, that's normal). The script is saved to a file first instead of being piped straight into a shell, so you can read it (`less wsl-setup.sh`) before it runs:
```bash
curl -fsSLo wsl-setup.sh https://raw.githubusercontent.com/rohan2pt0/ai-cloud-cyber-range/main/local/scripts/wsl-setup.sh
bash wsl-setup.sh
```
It downloads SecuRAX into Ubuntu's fast disk, keeps your old keys, starts everything and tells you when it's ready. The first start downloads a few GB — be patient.

## Step 3b — add your free API keys (makes answers instant)
Still in Ubuntu:
```bash
cd ~/securax && ./securax keys
```
For each of Gemini, Groq and OpenRouter it opens nothing for you — it prints the sign-up link, you create a free key there, paste it (typing is hidden) and press Enter. Press Enter on an empty line to skip one. It finishes with a **live test** showing which provider answered and how long it took.

## Step 4 — use it
Your Command Center opens in the browser by itself (or run `./securax open`, which prints the right address: `http://localhost:8088/hub.html`, or `https://hub.securax.localhost/hub.html` once HTTPS is on). Everything is linked from there.

## Step 5 — encrypt every connection (recommended, 3 minutes)
**First** (once): in the Guiding Map app open **Ops → System health → Export backup** — the app keeps its data per web address, and the secure address starts empty (you import the backup there, or use sync).
Your browser says "not secure" for `http://localhost…` because it is plain HTTP. Still in Ubuntu:
```bash
cd ~/securax && ./securax tls on
./securax tls trust --apply        # Windows asks you to confirm adding the SecuRAX authority: choose Yes, then close and reopen the browser
./securax down && ./securax up
```
Then use **https://hub.securax.localhost/hub.html** (a name, no port; the old http addresses stop working on purpose). Details and limits: `docs/securax/40-ENCRYPTION-IN-TRANSIT.md`.

## Every day after that
Open **Ubuntu**, then:
| I want to… | Type |
|---|---|
| start | `cd ~/securax && ./securax up` |
| stop (free RAM) | `cd ~/securax && ./securax down` |
| update to the latest | `cd ~/securax && ./securax update` |
| something is wrong | `cd ~/securax && ./securax doctor` |
| add / change an API key | `cd ~/securax && ./securax keys` |

Or from PowerShell, in the old Windows folder, the same commands work as `.\securax.cmd up` (it automatically uses the fast Ubuntu copy once Step 3 is done).

## If something fails
Copy **everything** the window printed and paste it to me. Don't try to fix it yourself.
