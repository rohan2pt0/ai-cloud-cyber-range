#!/usr/bin/env python3
"""WHY — turn the last lines of a container log into one plain-English sentence (stdin -> stdout; empty when nothing is recognised).

Used by `./securax why`. Patterns are ordered most-specific first and each hint says what to DO, never "delete the data".
"""
from __future__ import annotations

import re
import sys

HINTS = [
    (r"no space left on device", "The disk is full. Free space (./securax storage shows where it goes), then ./securax up."),
    (r"address already in use|port is already allocated|bind: .*in use", "Another program is already using this port. Close it (or run ./securax down, then ./securax up)."),
    (r"out of memory|\bOOM\b|\bKilled\b|exit(ed)? (with )?code 137", "It ran out of memory and Windows/Docker killed it. Close heavy apps, or run ./securax profile to right-size for your RAM."),
    (r"x509|certificate (verify|has expired|signed by unknown)|tls: ", "A certificate problem. Run ./securax tls status; ./securax tls on regenerates what is missing."),
    (r"database is locked|alembic|sqlalchemy\.exc|psycopg|could not open (the )?database|migration", "The app could not open its database. Take a backup first (./securax backup), then ./securax down and ./securax up. Do not delete the data volume."),
    (r"secret[_ ]key|WEBUI_SECRET|missing required (env|variable)|environment variable .* (not set|is required)", "A required secret/setting is missing. Run ./securax setup (it fills the missing ones) and then ./securax up."),
    (r"permission denied", "A file permission problem on a mounted folder. On Windows keep the project inside WSL (~/securax), not under /mnt/c."),
    (r"connection refused|econnrefused|could not connect|name or service not known|no route to host", "It started before something it depends on was ready. Wait a minute and run ./securax up again; if it repeats, ./securax why <the other service>."),
    (r"traceback \(most recent call last\)|unhandled exception|panic:|fatal error", "The app crashed while starting. You may be on an old version: run ./securax update."),
]


def hint(log: str) -> str:
    low = log.lower()
    for pat, text in HINTS:
        if re.search(pat, low, re.I):
            return text
    return ""


if __name__ == "__main__":
    h = hint(sys.stdin.read())
    if h:
        print(h)
