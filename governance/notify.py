#!/usr/bin/env python3
"""ChatOps without a lock-in: push the estate's plain-words digest to ANY chat that accepts an incoming
webhook (Mattermost, Slack, Rocket.Chat... all take {"text": "..."}). Off until you set one URL.

    ./securax notify test               send "SecuRAX is connected" (proves the webhook)
    ./securax notify digest [--dry-run] cockpit status + next 3 actions + incident deadlines, as one message
    ./securax notify digest --only-bad  stay silent when everything is green (quiet by default for humans)

    SECURAX_NOTIFY_WEBHOOK   the incoming-webhook URL. A secret: keep it in .env, never in git.
    SECURAX_NOTIFY_ALLOW_PLAIN_HTTP=1   allow http:// to a non-local host (default: https only, or http to localhost / private LAN)

What leaves the box: counts, labels and deadlines only. Never prompts, case narratives, tokens or file contents.
Exit codes: 0 sent or nothing to say, 1 send failed, 2 not configured.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import pathlib
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_LEN = 3500
ICON = {"green": "🟢", "amber": "🟠", "red": "🔴"}


def webhook() -> str | None:
    return os.environ.get("SECURAX_NOTIFY_WEBHOOK", "").strip() or None


def url_problem(url: str) -> str | None:
    """Refuse a webhook that would send estate data over cleartext to the open internet."""
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return "webhook must be an http(s) URL"
    if u.scheme == "https" or os.environ.get("SECURAX_NOTIFY_ALLOW_PLAIN_HTTP") == "1":
        return None
    host = u.hostname
    if host == "localhost":
        return None
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_loopback or ip.is_private:
            return None
    except ValueError:
        if host.endswith((".local", ".ts.net", ".internal")):           # LAN / Tailscale names
            return None
    return "plain http to a non-local host is refused (use https, or set SECURAX_NOTIFY_ALLOW_PLAIN_HTTP=1)"


def post(url: str, text: str, timeout: int = 10) -> None:
    body = json.dumps({"text": text[:MAX_LEN]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:      # noqa: S310 (scheme validated by url_problem)
        if r.status >= 300:
            raise OSError(f"webhook answered {r.status}")


def _run_json(argv: list[str]) -> dict:
    p = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=300)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {}


def incident_lines() -> list[str]:
    p = subprocess.run([sys.executable, str(ROOT / "governance" / "incident.py"), "due", "--within", "24"],
                       cwd=ROOT, text=True, capture_output=True, timeout=60)
    return [ln for ln in p.stdout.splitlines() if ln.startswith(("OVERDUE", "DUE SOON"))]


def build_digest(cockpit: dict | None = None, incidents: list[str] | None = None) -> tuple[str, str]:
    """(status, message). Status is the cockpit's overall colour: green / amber / red / unknown."""
    c = cockpit if cockpit is not None else _run_json([sys.executable, str(ROOT / "governance" / "cockpit.py"), "--json", "--fast"])
    inc = incidents if incidents is not None else incident_lines()
    status = c.get("overall") or "unknown"
    lines = [f"{ICON.get(status, '⚪')} **SecuRAX estate: {status.upper()}**"]
    todo = (c.get("eisenhower") or {}).get("do") or []
    if todo:
        lines.append("**Do now**")
        lines += [f"- {t}" for t in todo[:3]]
    if inc:
        lines.append("**Regulatory clock**")
        lines += [f"- {ln}" for ln in inc[:5]]
    if not todo and not inc:
        lines.append("Nothing urgent.")
    lines.append("Cockpit: http://localhost:8088/portal/cockpit.html")
    return status, "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("test")
    d = sub.add_parser("digest")
    d.add_argument("--dry-run", action="store_true", help="print the message, send nothing")
    d.add_argument("--only-bad", action="store_true", help="send only when amber/red or a deadline is near")
    a = ap.parse_args(argv)

    if a.cmd == "digest":
        status, msg = build_digest()
        if a.dry_run:
            print(msg)
            return 0
        if a.only_bad and status == "green" and "Regulatory clock" not in msg:
            print("all green: nothing sent")
            return 0
    else:
        msg = "✅ SecuRAX is connected to this channel."
    url = webhook()
    if not url:
        print("not configured: set SECURAX_NOTIFY_WEBHOOK (a Mattermost/Slack incoming-webhook URL) in .env")
        return 2
    bad = url_problem(url)
    if bad:
        print("refused: " + bad)
        return 2
    try:
        post(url, msg)
    except Exception as e:                                         # the URL is a secret: never echo it
        print(f"send failed: {type(e).__name__}")
        return 1
    print("sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
