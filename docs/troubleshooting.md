# Troubleshooting

Start here: **`./securax why`** shows what stopped and why, and **`./securax doctor`** checks health and runs a real chat
test. The table below comes from real installs.

## Terminal and setup

| Symptom | Cause | Fix |
|---|---|---|
| `./securax: No such file or directory` | you are in another folder | `cd ~/securax` (or run `./securax shortcut` once, then `securax <command>` from anywhere) |
| The terminal shows `>` and waits | a pasted block included the ```` ``` ```` fence lines, or an unclosed quote | **Ctrl+C**, then paste only the commands (use the copy button) |
| Commands after a `sudo` line printed nothing | the password prompt took the next pasted lines as the password | run `sudo …` lines on their own, type the password, press Enter |
| `docker: command not found` (WSL) | Docker Desktop's WSL integration is off for Ubuntu | Docker Desktop → Settings → Resources → WSL integration → Ubuntu → Apply & restart, then `wsl --shutdown` in PowerShell |
| `Docker is installed but not running` | Docker Desktop is not started | start it, wait for "Engine running" |
| `doctor` shows `curl: (52) Empty reply from server` | the gateway is starting or restarting | wait a minute, then `./securax why gateway` |
| `schedule: off` or `cron is not running` | cron is not set up, or WSL restarted without systemd | `./securax routines install` |

## AI and Chat

| Symptom | Cause | Fix |
|---|---|---|
| `chat: the default ladder FAILED` | no working cloud key and the local model is still loading | `./securax providers add gemini` (free), or wait for the model, then `./securax doctor` |
| `local model … NOT pulled` | first download not finished | `./securax pull` |
| Every request is blocked, "detector offline" | Llama Guard is on but not installed (fail-closed) | `./securax guard off` (built-in rails still enforce) |
| "That looks like an 'openrouter' key, not 'openrouter_pro'" | older version (shared keys were flagged) | `./securax update`; it is the same key, so answer `y` |
| A model name stopped working | the provider retired it | `./securax models` repairs model names |
| Chat signs you out after every update | an old install without a kept sign-in key | `./securax update` (the key is now kept in `.env`) |
| Out of memory, slow | the estate is larger than the RAM Docker has | `./securax profile`; on Windows raise `memory=` in `.wslconfig` |

## Phones, sync and alerts

| Symptom | Cause | Fix |
|---|---|---|
| The phone cannot open the address | the Tailscale toggle is off on the phone, or nothing is published | turn Tailscale on; on the laptop run `./securax phones` |
| Ask or sync fails on the phone | the app is opened from an old address, or the local HTTPS edge is on | open `https://<laptop>.<tailnet>.ts.net`; `./securax tls off && ./securax up` |
| `ntfy: sent` but nothing on the phone | the phone is subscribed to a different topic (a typo, or extra `/words`) | unsubscribe, then subscribe to exactly the topic `./securax notify setup` shows |
| It arrives but does not buzz | the topic was open on screen, or battery saving / quiet channel | close the app; Settings → Apps → ntfy → Battery → Unrestricted; allow sound for its notifications |
| Messages you did not send appear in ntfy | someone else knows the topic | `./securax notify setup --new` and subscribe to the new topic |

## Cockpit

| Symptom | Cause | Fix |
|---|---|---|
| "Oldest running software" stays red after updating | the age is the vendor's build date of a **pinned** image, so `update` cannot lower it | the tile names the image; stop it if unused (n8n: `./securax stop flows`), or wait for a release that raises the pin |

## Still stuck

Run these and keep the output (it contains no keys):

```bash
./securax why
./securax doctor
```
