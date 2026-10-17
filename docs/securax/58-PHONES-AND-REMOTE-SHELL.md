# 58 · Phones over Tailscale, and a shell on the laptop from your phone

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and tested in CI; not yet verified on a real phone (the sandbox has no second device). [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Two things, both through your own tailnet (WireGuard, authenticated by your Tailscale login). Nothing is opened to the
internet and no router port is forwarded.

## 1. The app, Ask, sync and Chat on every device: one address

The app's own web server (port 8088) now forwards the AI gateway (`/v1`, `/healthz`) and the sync service (`/sync`).
Phones therefore need **one** address. The browser sees a single origin, so it needs no cross-origin permission, and
neither the gateway nor sync is published separately.

On the laptop:
```
./securax tls off        # only if the local HTTPS edge is on: Tailscale provides the HTTPS instead
./securax up
```
`./securax phones` checks what is in the way (HTTPS edge, app port, Tailscale signed in) and prints the steps with
**your** address. `./securax phones --apply` runs the two `serve` commands on Windows for you through WSL interop.

Or, in **Windows PowerShell**, after installing Tailscale and turning on MagicDNS and HTTPS certificates in the admin console:
```
tailscale serve --bg 8088                    # app + Ask + sync    → https://<laptop>.<tailnet>.ts.net
tailscale serve --bg --https=10000 3000      # Chat (Open WebUI)   → https://<laptop>.<tailnet>.ts.net:10000
tailscale serve status
```
**Never `tailscale funnel`:** it publishes to the whole internet.

What the app does on a `*.ts.net` address:

| Feature | Address it uses |
|---|---|
| Ask | the same address. The gateway key field is needed only if `./securax gateway-auth enable` is on |
| Cross-device sync | defaults to `https://<laptop>.<tailnet>.ts.net/sync` (token from `SYNC_TOKENS` in `.env`, user `me` on every device) |
| Chat links | port 10000 of the same name |

Each address keeps its own app data. Export from the old address (Ops → backup) before switching, or let sync carry it.

**The router key** (`LITELLM_MASTER_KEY`) shipped as the placeholder `sk-range-change-me`. `./securax up` now replaces it
once with a strong random key in `.env`. Every service reads it from `.env` when it starts. Chat's configuration is not
persisted (`ENABLE_PERSISTENT_CONFIG=false`), so nothing else needs changing.

## 2. A shell on the laptop's WSL from your phone, anywhere

Recommended: **Tailscale inside WSL with Tailscale SSH**. WSL becomes its own tailnet device (for example `laptop-wsl`).

| Property | How |
|---|---|
| No passwords or SSH keys to manage | Tailscale SSH authenticates with your tailnet identity |
| Re-checks who you are | `check` mode: a fresh browser login every 12 hours by default |
| No port 22 on Wi-Fi or the internet | sshd is not installed or opened; only tailnet peers your policy allows can connect |
| Works on mobile data | Tailscale on the phone works on any network |

### On the laptop (WSL Ubuntu, systemd on)
Install from Tailscale's official apt repository rather than `curl | sh`:
```
. /etc/os-release
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/$VERSION_CODENAME.noarmor.gpg | sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/$VERSION_CODENAME.tailscale-keyring.list | sudo tee /etc/apt/sources.list.d/tailscale.list
sudo apt-get update && sudo apt-get install -y tailscale tmux
sudo tailscale up --ssh --hostname=laptop-wsl
```
Open the login link it prints and sign in with the **same** Tailscale account.

### Keep it reachable
- **WSL stops when idle.** Add a Windows Task Scheduler task "At log on" that runs `wsl.exe -d Ubuntu --exec sleep infinity`, hidden.
- **The laptop must be awake.** Windows → Power → When plugged in, sleep **Never**; lid close **Do nothing** (on AC power).
- Use **tmux** so a dropped mobile connection does not kill a running command: `tmux new -A -s main`.

### On the OnePlus 10R
1. Tailscale app on, same account.
2. Install **Termux from F-Droid** (the Play Store build is outdated). Run `pkg install openssh`, then `ssh <your-linux-user>@laptop-wsl`.
   A GUI client such as Termius also works. The first connection opens a browser check.
3. Then: `tmux new -A -s main`, `cd ~/securax`, and run any `./securax` command.

### Harden the tailnet (5 minutes, once)
- **MFA** on the account you sign in to Tailscale with (Google/Microsoft/GitHub). The tailnet is only as strong as that login.
- **Keep the SSH rule in `check` mode** in the access policy, with destination `autogroup:self`. Only your own devices, as a non-root user.
- **Leave device key expiry on**, and re-authenticate when asked.
- Optional: **Tailnet Lock**, so a new device needs your signature from a device you already trust.
- **Remove lost devices** from the admin console at once.
- **Never** put a bank-issued device on this tailnet, and never reach bank systems from it.

### Not recommended
| Option | Why not |
|---|---|
| Port-forwarding 22 on the home router + OpenSSH | exposed to the whole internet, and the ISP may use CGNAT anyway |
| Windows OpenSSH server + `wsl` | a second login surface on Windows, with keys or passwords to manage |
| Cloud "remote desktop" relays | a third party in the path, and more than you need for a shell |

## Update: the HTTPS edge and phones together

`./securax tls on` no longer has to be off for phones. The edge listens on two loopback-only device ports (9443 app, 9444
Chat) and `./securax phones --apply` (or `./securax go`) points `tailscale serve` at them. The laptop keeps
`https://hub.securax.localhost`, and phones use the ts.net name. Details: doc 67, section 5.
