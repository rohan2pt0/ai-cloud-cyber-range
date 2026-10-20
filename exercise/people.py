"""The people in the range: simulated staff who keep working, and a red-team bot that tries the doors staff leave open.

User simulation. Each round, every staff account in the scenario logs in over SSH to one of its machines and reads its
notes, with the password the blue team last DOCUMENTED (portal: Staff password changes), or the original one. A login that
fails costs availability points, exactly as when a team changes a password without telling the exercise.

Red-team bot. Only in a phase where attacks are allowed, it tries the scenario's ORIGINAL admin and staff passwords on the
machines it can reach. A login that works is an attack report against the team (source "bot"), with the account as evidence,
and a harmless marker file is left in /tmp so the blue team can find it. It does nothing else: it is a baseline adversary
that punishes the one mistake every team must fix first, while human red teamers do the rest.

Passwords reach ssh through the SSHPASS environment variable, never the command line, so `ps` does not show them.
Host keys are not checked: range machines are rebuilt often, and the range networks are closed to everything else.
"""
from __future__ import annotations

import os
import random
import subprocess
import time

from . import scenario as scn

SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=5", "-o", "LogLevel=ERROR",
            "-o", "PreferredAuthentications=password,keyboard-interactive", "-o", "PubkeyAuthentication=no", "-o", "NumberOfPasswordPrompts=1"]


def ssh_run(ip: str, user: str, password: str, command: str, timeout: int = 20) -> tuple[bool, str]:
    try:
        p = subprocess.run(["sshpass", "-e", "ssh", *SSH_OPTS, f"{user}@{ip}", command], capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "SSHPASS": password})
    except (OSError, subprocess.SubprocessError) as e:
        return False, type(e).__name__
    if p.returncode == 0:
        return True, "logged in"
    if p.returncode == 5 or "Permission denied" in p.stderr:
        return False, "wrong password"
    return False, ("could not connect" if p.returncode == 255 else f"exit {p.returncode}") + (": " + p.stderr.strip()[:80] if p.stderr.strip() else "")


def ssh_key_run(ip: str, user: str, key: str, command: str, timeout: int = 20) -> tuple[bool, str]:
    try:
        p = subprocess.run(["ssh", "-i", key, "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", "-o", "PasswordAuthentication=no",
                            *SSH_OPTS[:8], f"{user}@{ip}", command], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return False, type(e).__name__
    return p.returncode == 0, (p.stdout.strip() or p.stderr.strip())[:120]


def rule_checks(game, team: int, deployed: set[str], key: str | None, run=ssh_key_run) -> list[tuple[str, str, bool, str]]:
    """The rules a machine can prove each round. Today: the green-team account still logs in with its key and is still an
    administrator. (Ping must stay allowed too: that is the HOST check every machine already has.)"""
    sc = game.scenario(team)
    gt = sc.get("green_team")
    if not gt or not key:
        return []
    out = []
    for name in sorted(deployed):
        if not _ssh_host(sc, name, deployed):
            continue
        h = scn.host(sc, name)
        ok, why = run(h["ip"], gt["username"], key, "id -nG")
        if ok and "wheel" not in why.split():
            ok, why = False, "the green-team account is no longer an administrator"
        out.append((name, "Green-team account works", ok, "logs in with its key and is an administrator" if ok else why or "key login refused"))
    return out


def _ssh_host(sc: dict, name: str, deployed: set[str]) -> dict | None:
    h = scn.host(sc, name)
    if name in deployed and any(s["check"] == "ssh" for s in h.get("services", [])):
        return h
    return None


def usersim(game, team: int, deployed: set[str], run=ssh_run, rng: random.Random | None = None) -> list[tuple[str, str, bool, str]]:
    sc = game.scenario(team)
    rng = rng or random.Random()
    out = []
    for u in sc["users"]:
        options = [h for h in (_ssh_host(sc, n, deployed) for n in u.get("hosts", [])) if h]
        if not options:
            continue
        h = rng.choice(options)
        ok, why = run(h["ip"], u["username"], game.password(team, u["username"], h["name"]), "cat ~/notes.txt >/dev/null && ls ~ >/dev/null")
        out.append((u["username"], h["name"], ok, why))
    return out


def redbot_round(game, team: int, deployed: set[str], reach: set[str], run=ssh_run, now: float | None = None) -> list[int]:
    """One pass over reachable machines with the original passwords. Returns the ids of the attacks it reported."""
    if not game.phase(now).get("attacks_allowed"):
        return []
    sc = game.scenario(team)
    already = game.compromised(team, now)
    tried: list[int] = []
    for h in sc["hosts"]:
        if h["zone"] not in reach or h["name"] in already or not _ssh_host(sc, h["name"], deployed):
            continue
        accounts = [(sc["admin"]["username"], sc["admin"]["password"])] + [(u["username"], u["password"]) for u in sc["users"] if h["name"] in u.get("hosts", [])]
        for user, pw in accounts:
            stamp = int(now or time.time())
            ok, _ = run(h["ip"], user, pw, f"echo 'red team was here at {stamp}' > /tmp/.redteam-{stamp} && id -un")
            if ok:
                tried.append(game.attack(team, "red-bot", h["name"], f"Logged in as {user} with the scenario's original password",
                                         f"ssh {user}@{h['ip']} succeeded; marker /tmp/.redteam-{stamp}", source="bot"))
                break
    return tried
