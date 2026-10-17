# Quickstart

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** Every command exists and runs in CI; the Windows + WSL path was verified on one real install. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

Install SecuRAX, start it, and get a real chat answer. About 30 minutes, most of it downloads.

!!! tip "Copying commands"
    Use the copy button at the top right of each code block. Run commands **one block at a time**. If the terminal
    shows a `>` prompt, press **Ctrl+C**: something incomplete was pasted.

## Before you begin

| You need | Notes |
|---|---|
| 16 GB RAM (8 GB works in lite mode) | `./securax profile` sizes everything to your machine |
| About 15 GB free disk | models and images |
| Docker | Windows/macOS: Docker Desktop. Linux: Docker Engine + Compose |
| Windows only: WSL 2 with Ubuntu | Docker Desktop → Settings → Resources → **WSL integration** → turn on **Ubuntu** |

!!! warning "Personal machine only"
    Never install SecuRAX on a bank-issued or employer-managed device.

## 1. Get the code

=== "Windows (Ubuntu in WSL)"

    ```bash
    cd ~
    git clone https://github.com/rohan2pt0/ai-cloud-cyber-range.git securax
    cd ~/securax
    ```

=== "macOS / Linux"

    ```bash
    git clone https://github.com/rohan2pt0/ai-cloud-cyber-range.git securax
    cd securax
    ```

Check that Docker is reachable from this terminal:

```bash
docker ps
```

`command not found` on Windows means WSL integration is off (see the table above).

## 2. Set up and start

```bash
./securax setup
```

The guided setup asks for free AI keys (input is hidden) and sizes the estate to your machine. Then one command does the
rest (start, schedules, phones, backup, sync) and ends with one status screen:

```bash
./securax go
```

Every line should show ✔. A ✗ line names its one fix. `./securax doctor` adds a real chat test (it should end with
**`chat: WORKS ✔`**). Make the command available from any folder:

```bash
./securax shortcut
```

## 3. Protect it

```bash
./securax residency enable --jurisdiction IN
./securax protect
```

The first command keeps Red-tier (personal, bank-related) data on the local model. The second encrypts backups.
**Keep the backup key in your password manager.**

## 4. Alerts and schedule

```bash
./securax notify setup
./securax routines install
```

`notify setup` creates a private ntfy topic and sends a test once you subscribe to it in the ntfy app.
`routines install` starts the scheduled jobs (health brief, backups, AI-history import).

## 5. Phones and tablets

```bash
./securax phones
```

It checks what is in the way and prints the exact steps with your own address. See
[Phones and remote shell](../securax/58-PHONES-AND-REMOTE-SHELL.md).

## Every day

| When | Where | What |
|---|---|---|
| Morning, 2 min | Guiding Map → Today | check-in, the one open action |
| Any question | Chat → Twin (Twin-private for anything personal) | ask |
| An alert arrives | ntfy | only when something needs you |
| Weekly | `./securax cockpit` | the three "Do now" items |
| Something is off | `./securax why` | what stopped and why |

## Keep it current

```bash
./securax update
```

`update` backs up first, health-checks the new version and rolls back automatically if it does not start.
