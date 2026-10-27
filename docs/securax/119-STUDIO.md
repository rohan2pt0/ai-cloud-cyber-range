# Code Studio — build the estate from a browser, on your own models

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** Built and shipped as the usable first version: ./securax studio starts VS Code + the Cline AI coding agent in the browser (codercom/code-server, digest-pinned) as an opt-in add-on that is never part of the core start, reached by name at hub.<domain>/studio/ through the edge, with a generated password and Cline pointed at your own gateway (OpenAI-compatible) so building the estate needs no Claude and no terminal. Amber until the queued hardening lands (non-root, a code.<domain> subdomain option, gateway-identity sign-in, a sandbox journey that proves the page loads and Cline reaches the gateway, and a digest-pin watch). A standalone docker-run fallback is documented for the first run. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The friction this removes:** until now, changing SecuRAX meant a terminal and a paid Claude Code
subscription — a single point of failure over the estate's whole purpose, sovereignty. Code Studio puts
a familiar GUI (VS Code) with an AI coding agent (**Cline**) in your browser, pointed at **your own
gateway** and the open models you already run. You edit files, run commands, use git and MCP
connectors, and the agent writes code — with **no Claude and no terminal**.

## One command

```bash
./securax studio            # start it, print the address + a generated password
./securax studio open       # open it in your browser
./securax studio status     # is it running?
./securax studio down       # stop it (your estate is untouched)
```

It is an **opt-in add-on**: it has its own profile and is **never part of `./securax up`**, so it can
never affect your running estate. It is reached by name at **`https://hub.<domain>/studio/`** (no raw
port), through the same HTTPS edge as the rest of the estate.

## First run (one time, ~2 minutes)

1. `./securax studio` — the first start pulls the image and installs the Cline extension (a minute or
   two). It prints the address and a **generated password** (saved as `STUDIO_PASSWORD` in
   `local/compose/.env`). Open the address, sign in with that password.
2. In the **Cline** sidebar (the robot icon) → **Settings → API Provider: “OpenAI Compatible”**:
   - **Base URL:** `http://gateway:8080/v1`  *(the gateway, reached by name from inside Studio — note the `/v1`, a missing or extra `/v1` is the usual reason a model “hangs”)*
   - **API key:** your gateway key *(leave blank if gateway auth is off, the laptop default)*
   - **Model:** a coding-capable model from your ladder — see `./securax opencode --check`
3. Ask Cline to do something small to confirm the handshake (“list the files in this repo”). From then
   on, drive it like Claude Code: describe the change, review its plan, let it edit and run.

Your projects are just folders; MCP connectors are configured in Cline’s MCP settings the same way.

## Security

- Studio can run code, so it is **never left open**: a strong password is generated on first start.
  Set your own by putting `STUDIO_PASSWORD=…` in `local/compose/.env` before starting.
- It binds to **loopback only** and is reached through the edge, like the other services.
- The repository is mounted so the agent can change it — that is the point; keep the password private.

## If the in-browser editor misbehaves (fallback)

Serving a full IDE under a sub-path through two proxies is the one part that only your first real run
can confirm. If the editor loads oddly or a panel won’t connect, you are not stuck — run the
**standalone** version, which talks to the same gateway and models:

```bash
docker run -d --name securax-studio \
  --add-host=host.docker.internal:host-gateway \
  -p 127.0.0.1:8443:8080 \
  -v "$HOME/ai-cloud-cyber-range:/home/coder/project" \
  -v securax-studio-data:/home/coder/.local/share/code-server \
  -e PASSWORD='choose-a-strong-one' \
  codercom/code-server:4.143.1 \
  --install-extension saoudrizwan.claude-dev --bind-addr 0.0.0.0:8080
# open http://localhost:8443  — Cline base URL: http://host.docker.internal:8080/v1
```

## What is still queued (hardening)

This is the usable first version (shipped per *build usable today, harden after*). Tracked follow-ups
(`governance/queue.json`, `studio-harden`):

- Run the container as a **non-root** user with a scoped mount (not the whole home).
- Offer Studio as its **own subdomain** (`code.<domain>`) as well as the `/studio/` path, for editors
  that prefer a root path.
- **Sign-in through the gateway’s identity** (OIDC) instead of a shared password.
- A **sandbox journey** that starts Studio, proves the page loads over the edge and that Cline reaches
  the gateway, so CI tests it on every change.
- Pin the image in `digest-pins.json` and let the weekly supply-chain watch track it.

## Why this matters

With Studio, the estate builds itself: the models you own do the work, the GUI is one you already know,
and no outside service or paid plan gates your day-to-day changes. That is the sovereignty the whole
project is for — and the companion to [doc 118](118-BUILD-WITH-YOUR-MODELS.md), which drives the same
open models from the command line.
