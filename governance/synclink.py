#!/usr/bin/env python3
"""One tap to set up cross-device sync on a phone or another computer.

    ./securax sync-link [--user me] [--host 100.x.y.z]      prints a link; open it on the device and confirm once

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
    if tls_on:
        dom = env.get("SECURAX_DOMAIN", DEFAULT_DOMAIN)
        hub, sync = f"https://hub.{dom}/", f"https://sync.{dom}/sync"
    else:
        hub, sync = f"http://{host}:8088/", f"http://{host}:8089/sync"
    return f"{hub}#sync={encode(sync, tokens[token_index], user)}", sync


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--user", default="me", help="the name your data is stored under (use the same on every device)")
    ap.add_argument("--host", default="localhost", help="address of this machine as the OTHER device sees it (only when HTTPS is off)")
    ap.add_argument("--token", type=int, default=1, help="which of your sync tokens to use (default 1)")
    a = ap.parse_args(argv)
    link, sync = build(read_env(), a.user, a.host, a.token - 1)
    print(f"Open this on the other device (its data will be stored on {sync}):\n")
    print(link)
    print("\nIt contains your sync token: send it only over a channel you trust. The device must be able to reach that address.")
    if sync.startswith("http://") and a.host == "localhost":
        print("Note: 'localhost' only works on THIS machine. For a phone use  --host <this machine's Tailscale/LAN address>  (and turn on HTTPS: ./securax tls on).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
