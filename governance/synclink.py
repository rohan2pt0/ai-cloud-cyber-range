#!/usr/bin/env python3
"""One tap to set up cross-device sync on a phone or another computer.

    ./securax sync-link [--user me] [--host 100.x.y.z]      prints a link; open it on the device and confirm once
    With Tailscale on (doc 58) it prints TWO links: one for this laptop (localhost) and one for your phones (the ts.net name).

The link carries your sync address and device token in the part after '#', which browsers never send to any server. The app shows WHERE
your data will be stored before it saves anything, removes the token from the address bar at once, and never replaces an existing setup
without a second yes. Treat the link like a password: send it over a channel you trust (a private chat, AirDrop), not by public email.
Uses the HTTPS names when `./securax tls on` is active (https://hub.<domain>), otherwise the plain addresses on --host (default: this machine).
"""
from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENVF = ROOT / "local" / "compose" / ".env"
DEFAULT_DOMAIN = "securax.localhost"


def read_env(path: pathlib.Path = ENVF) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for ln in path.read_text("utf-8").splitlines():
            if ln.strip() and not ln.lstrip().startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def encode(url: str, key: str, user: str) -> str:
    raw = json.dumps({"url": url, "key": key, "user": user}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def build(env: dict[str, str], user: str = "me", host: str = "localhost", token_index: int = 0) -> tuple[str, str]:
    """(link, where-the-data-goes). Raises SystemExit with a plain message when sync is not set up."""
    tokens = [t.strip() for t in env.get("SYNC_TOKENS", "").split(",") if t.strip()]
    if not tokens:
        raise SystemExit("No sync token yet. Run  ./securax setup  (it creates one), then try again.")
    if not 0 <= token_index < len(tokens):
        raise SystemExit(f"There are {len(tokens)} sync token(s); --token must be 1..{len(tokens)}.")
    tls_on = "tls.yml" in env.get("COMPOSE_FILE", "")
    if host.endswith(".ts.net"):                        # phones: Tailscale's own HTTPS name, sync on the same origin (edge on or off)
        hub, sync = f"https://{host}/", f"https://{host}/sync"
    elif tls_on:                                        # sync on the hub's own origin: sync.<domain> is another origin, which the app may not call
        dom = env.get("SECURAX_DOMAIN", DEFAULT_DOMAIN)
        hub, sync = f"https://hub.{dom}/", f"https://hub.{dom}/sync"
    else:                                               # the app proxies /sync on its own origin (no cross-origin call, no 2nd port)
        hub, sync = f"http://{host}:8088/", f"http://{host}:8088/sync"
    return f"{hub}#sync={encode(sync, tokens[token_index], user)}", sync


def tailscale_name() -> str:
    """This machine's Tailscale name (rc.tailXXXX.ts.net), via the Windows or Linux CLI; '' when Tailscale is not on."""
    import shutil
    import subprocess
    for exe in ("tailscale.exe", "/mnt/c/Program Files/Tailscale/tailscale.exe", "tailscale"):
        if shutil.which(exe) or pathlib.Path(exe).is_file():
            try:
                out = subprocess.run([exe, "status", "--json"], capture_output=True, text=True, timeout=10).stdout
                return str(json.loads(out)["Self"]["DNSName"]).rstrip(".")
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                return ""
    return ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--user", default="me", help="the name your data is stored under (use the same on every device)")
    ap.add_argument("--host", default="localhost", help="address of this machine as the OTHER device sees it (only when HTTPS is off)")
    ap.add_argument("--token", type=int, default=1, help="which of your sync tokens to use (default 1)")
    ap.add_argument("--print-only", choices=["laptop", "phone"], help="print just that one link (used by ./securax go)")
    a = ap.parse_args(argv)
    env = read_env()
    if a.print_only:
        print(build(env, a.user, a.host if a.print_only == "phone" else "localhost", a.token - 1)[0])
        return 0
    link, sync = build(env, a.user, a.host, a.token - 1)
    ts = tailscale_name() if a.host == "localhost" else ""          # phones work with the HTTPS edge on too (device ports, doc 58)
    print("THIS LAPTOP: open this link in the browser you use for the app (or the installed app), then confirm once:\n")
    print(link)
    if ts:
        print("\nYOUR PHONES (Tailscale on): open this link on each phone, then confirm once:\n")
        print(build(env, a.user, ts, a.token - 1)[0])
    print("\nYour data comes back by itself on every device after that: nothing to fill in again.")
    print("Each link contains your sync token: send it only over a channel you trust, and never paste it into a chat.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
