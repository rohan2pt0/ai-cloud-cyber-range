#!/usr/bin/env python3
"""One file that says what is wrong, with nothing private in it: the estate's support packet.

    ./securax support-packet            write vault/support/securax-support-<time>.zip and list what is inside
    ./securax support-packet --print    show the packet's text on screen instead (nothing is written)

Modelled on Mattermost's support packet. When something breaks, a helper needs the versions, the health check, what is
running and the recent errors, and not your keys, notes or data. So the packet holds:

- **versions.txt:** the release and build, the operating system, Python, Docker and Git.
- **health.txt:** `./securax doctor` (cut off after 90 seconds).
- **containers.txt:** what Docker is running, and each container's state.
- **settings.txt:** every setting's NAME in local/compose/.env, with its value replaced by `<set>` or `<empty>`.
- **routines.txt:** each routine's last runs (time, exit code, whether it flagged anything).
- **log-tail.txt:** the last 200 lines of the routines log.

Before anything is written, the logs and outputs are scrubbed: e-mail addresses, keys and tokens, long digit runs
(card, account and phone numbers), and your home folder's path become `<redacted>`. Read the packet before you
share it; it is yours to send or not. Standard library only; works with the estate stopped.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import pathlib
import platform
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "vault" / "support"

_SCRUB = [
    (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"), "<email>"),
    (re.compile(r"(?i)\b(bearer|token|key|secret|password|passwd|pwd)\b(\s*[:=]\s*|\s+)\S+"), r"\1\2<redacted>"),
    (re.compile(r"\b(sk|pk|ghp|gho|github_pat|xox[abpr]|AKIA|AIza)[-_A-Za-z0-9]{12,}"), "<key>"),
    (re.compile(r"\beyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{5,}"), "<jwt>"),
    # card, Aadhaar and phone shapes (groups of 4, two groups of 5) and any 10-19 digit run; dates and times stay readable
    (re.compile(r"\b(?:\d{4}[ -]){2,4}\d{1,4}\b|\b\d{5}[ -]\d{5}\b|\b\d{10,19}\b"), "<number>"),
]


def scrub(text: str, home: str = "") -> str:
    """The text with personal and secret values replaced; `home` (your home folder) becomes ~."""
    home = home or str(pathlib.Path.home())
    if len(home) > 1:
        text = text.replace(home, "~")
    for rx, sub in _SCRUB:
        text = rx.sub(sub, text)
    return text


def settings(env_file: pathlib.Path) -> str:
    """NAME=<set> / NAME=<empty> for each line of an .env file: the shape of the settings, never their values."""
    try:
        lines = env_file.read_text("utf-8", "ignore").splitlines()
    except OSError:
        return "(no local/compose/.env yet: the estate has not been set up on this machine)\n"
    out = []
    for ln in lines:
        m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)", ln)
        if m:
            out.append(f"{m.group(1)}=<{'set' if m.group(2).strip().strip(chr(34)).strip(chr(39)) else 'empty'}>")
    return "\n".join(out) + "\n"


def routines(history: pathlib.Path) -> str:
    try:
        hist = json.loads(history.read_text("utf-8"))
    except (OSError, ValueError):
        return "(no routine runs recorded yet)\n"
    out = []
    for jid in sorted(hist):
        runs = hist[jid][-5:]
        out.append(f"{jid}: " + ", ".join(f"{r.get('t', '?')} code {r.get('code', '?')}{' flagged' if r.get('found') else ''}" for r in runs))
    return "\n".join(out) + "\n"


def _run(cmd: list[str], timeout: int = 20) -> str:
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip() or f"(no output, exit {r.returncode})"
    except FileNotFoundError:
        return f"({cmd[0]} is not installed)"
    except subprocess.TimeoutExpired:
        return f"(stopped after {timeout} s)"


def _tail(path: pathlib.Path, n: int = 200) -> str:
    try:
        return "\n".join(path.read_text("utf-8", "ignore").splitlines()[-n:]) + "\n"
    except OSError:
        return "(no routines log yet)\n"


def collect(root: pathlib.Path = ROOT, quick: bool = False) -> dict[str, str]:
    """{file name: scrubbed text}. `quick` skips the slow outside commands (doctor, docker), for tests and --print."""
    try:
        version = (root / "VERSION").read_text("utf-8").strip()
    except OSError:
        version = "unknown"
    build = _run([sys.executable, str(root / "governance" / "buildinfo.py")])
    files = {
        "versions.txt": "\n".join([
            f"SecuRAX {version} · build {build}",
            f"Made {dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %z')}",
            f"OS: {platform.system()} {platform.release()} ({platform.machine()})" + (" · WSL" if "microsoft" in platform.release().lower() else ""),
            f"Python {platform.python_version()}",
            "Docker: " + ("(skipped)" if quick else _run(["docker", "version", "--format", "{{.Server.Version}}"])),
            "Git: " + _run(["git", "--version"]),
            "Code: " + _run(["git", "-C", str(root), "status", "--short", "--branch", "--untracked-files=no"]).splitlines()[0],
        ]) + "\n",
        "settings.txt": settings(root / "local" / "compose" / ".env"),
        "routines.txt": routines(root / "routines" / ".history.json"),
        "log-tail.txt": _tail(root / "routines" / ".log"),
    }
    if not quick:
        files["health.txt"] = _run([str(root / "securax"), "doctor"], timeout=90) + "\n"
        files["containers.txt"] = _run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"]) + "\n"
    return {k: scrub(v) for k, v in files.items()}


def write(files: dict[str, str], out_dir: pathlib.Path = OUT_DIR, now: dt.datetime | None = None) -> pathlib.Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"securax-support-{(now or dt.datetime.now()).strftime('%Y%m%d-%H%M')}.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", "SecuRAX support packet. Scrubbed of e-mails, keys, long numbers and your home path; "
                                 "settings show names only. Read it before you share it.\n")
        for name, text in sorted(files.items()):
            z.writestr(name, text)
    path.write_bytes(buf.getvalue())
    os.chmod(path, 0o600)
    return path


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if argv and argv[0] == "--print":
        for name, text in collect(quick=True).items():
            print(f"── {name}\n{text}")
        return 0
    print("Collecting (about a minute: it runs the health check)…")
    path = write(collect())
    rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    print(f"✔ {rel}")
    print("  Inside: versions, health check, containers, setting NAMES (no values), routine runs, the last 200 log lines.")
    print("  Scrubbed: e-mails, keys and tokens, long numbers, your home folder's path.")
    print(f"  Read it first:  python3 -m zipfile -l {rel}   then attach it to a bug report (Life OS → ⋯ → Report a problem).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
