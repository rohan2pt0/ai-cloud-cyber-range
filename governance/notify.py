#!/usr/bin/env python3
"""The estate's andon cord: push the plain-words digest to your phone (ntfy) and/or ANY chat that accepts an
incoming webhook (Mattermost, Slack, Rocket.Chat... all take {"text": "..."}). Off until you set one URL.

    ./securax notify test               send "SecuRAX is connected" (proves every configured channel)
    ./securax notify digest [--dry-run] cockpit status + next 3 actions + incident deadlines, as one message
    ./securax notify digest --only-bad  stay silent when everything is green (quiet by default for humans)
    ./securax notify digest --changed   send only when the picture CHANGED since the last send (incl. "back to green");
                                        the routine `andon` runs this every 15 minutes
    ./securax notify send "text" [--title T] [--priority high]   one message from any script or routine

    SECURAX_NOTIFY_NTFY      phone push: https://ntfy.sh/<a-long-random-topic> or your own ntfy server's topic URL.
                             The topic name is the password on the public server: make it long and random.
    SECURAX_NOTIFY_NTFY_TOKEN   optional access token (self-hosted ntfy with access control)
    SECURAX_NOTIFY_WEBHOOK   the incoming-webhook URL. A secret: keep it in .env, never in git.
    SECURAX_NOTIFY_ALLOW_PLAIN_HTTP=1   allow http:// to a non-local host (default: https only, or http to localhost / private LAN)
    All of these are read from the environment or, failing that, from local/compose/.env.

What leaves the box: counts, labels and deadlines only. Never prompts, case narratives, tokens or file contents.
Exit codes: 0 sent or nothing to say, 1 send failed, 2 not configured.
"""
from __future__ import annotations

import argparse
import hashlib
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


ENV_FILE = ROOT / "local" / "compose" / ".env"
STATE = ROOT / "vault" / "notify-state.json"


def env(name: str) -> str:
    """The environment first, then local/compose/.env (where `setup` and the docs tell you to put it)."""
    v = os.environ.get(name, "").strip()
    if v or not ENV_FILE.exists():
        return v
    for ln in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith(name + "="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def webhook() -> str | None:
    return env("SECURAX_NOTIFY_WEBHOOK") or None


def channels() -> list[tuple[str, str]]:
    """[(kind, url)] for every configured channel: ntfy (phone push) and/or a chat webhook."""
    out = []
    if env("SECURAX_NOTIFY_NTFY"):
        out.append(("ntfy", env("SECURAX_NOTIFY_NTFY")))
    if webhook():
        out.append(("webhook", webhook()))
    return out


def url_problem(url: str) -> str | None:
    """Refuse a webhook that would send estate data over cleartext to the open internet."""
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return "webhook must be an http(s) URL"
    if u.scheme == "https" or env("SECURAX_NOTIFY_ALLOW_PLAIN_HTTP") == "1":
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


PRIORITY = {"low": "2", "default": "3", "high": "4", "urgent": "5"}


def post_ntfy(url: str, text: str, title: str = "SecuRAX", priority: str = "default", timeout: int = 10) -> None:
    """ntfy takes the message as the plain body; title/priority/markdown travel as headers."""
    headers = {"Title": title.encode("ascii", "replace").decode(), "Priority": PRIORITY.get(priority, "3"), "Markdown": "yes"}
    tok = env("SECURAX_NOTIFY_NTFY_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, data=text[:MAX_LEN].encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:      # noqa: S310 (scheme validated by url_problem)
        if r.status >= 300:
            raise OSError(f"ntfy answered {r.status}")


DLQ = ROOT / "vault" / "notify-dlq.jsonl"
DLQ_MAX = 50


def with_retry(fn, attempts: int = 3, base: float = 0.5, sleep=None) -> None:
    """Call fn(); on failure wait base*2^n plus random jitter (so many senders do not retry in lockstep), then try again."""
    import random
    import time
    sleep = sleep or time.sleep
    for n in range(attempts):
        try:
            return fn()
        except Exception:
            if n == attempts - 1:
                raise
            sleep(base * (2 ** n) + random.uniform(0, base))


def _dlq_load(path: pathlib.Path | None = None) -> list[dict]:
    path = path or DLQ
    try:
        return [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]
    except (OSError, ValueError):
        return []


def _dlq_save(items: list[dict], path: pathlib.Path | None = None) -> None:
    path = path or DLQ
    if not items:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(i) + "\n" for i in items[-DLQ_MAX:]), "utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _send_one(kind: str, url: str, text: str, title: str, priority: str) -> None:
    with_retry(lambda: post_ntfy(url, text, title, priority) if kind == "ntfy" else post(url, text))


def deliver(text: str, title: str = "SecuRAX", priority: str = "default") -> int:
    """Send to every configured channel, retrying with backoff + jitter. A message that still cannot be sent goes to a
    dead-letter file (vault/notify-dlq.jsonl, newest 50) and is re-sent, marked "(delayed)", before the next message.
    At-least-once: a send whose reply was lost may arrive twice; an alert is never silently dropped.
    0 = all sent, 1 = a send failed (kept for later), 2 = nothing configured / refused."""
    chans = channels()
    if not chans:
        print("not configured: set SECURAX_NOTIFY_NTFY (phone push) or SECURAX_NOTIFY_WEBHOOK (Mattermost/Slack) in local/compose/.env")
        return 2
    rc, pending, still = 0, _dlq_load(), []
    for kind, url in chans:
        bad = url_problem(url)
        if bad:
            print(f"{kind}: refused: {bad}")
            rc = max(rc, 2)
            continue
        for old in [p for p in pending if p.get("kind") == kind]:            # earlier alerts first, in order
            try:
                _send_one(kind, url, "(delayed) " + old["text"], old.get("title", "SecuRAX"), old.get("priority", "default"))
                print(f"{kind}: delivered 1 delayed alert")
            except Exception:
                still.append(old)
        try:
            _send_one(kind, url, text, title, priority)
            print(f"{kind}: sent")
        except Exception as e:                                     # the URL is a secret: never echo it
            print(f"{kind}: send failed: {type(e).__name__} (kept; re-sent with the next alert)")
            still.append({"kind": kind, "text": text[:MAX_LEN], "title": title, "priority": priority})
            rc = 1
    _dlq_save(still + [p for p in pending if p.get("kind") not in {k for k, _ in chans}])
    return rc


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
    d.add_argument("--changed", action="store_true", help="send only when the digest differs from the last one sent")
    sn = sub.add_parser("send")
    sn.add_argument("text")
    sn.add_argument("--title", default="SecuRAX")
    sn.add_argument("--priority", choices=sorted(PRIORITY), default="default")
    a = ap.parse_args(argv)

    if a.cmd == "send":
        return deliver(a.text, a.title, a.priority)
    if a.cmd == "test":
        return deliver("✅ SecuRAX is connected to this channel.")

    status, msg = build_digest()
    if a.dry_run:
        print(msg)
        return 0
    if a.changed:
        if not channels():
            print("andon: no channel configured (set SECURAX_NOTIFY_NTFY in local/compose/.env); nothing sent")
            return 0
        digest = hashlib.sha256(msg.encode()).hexdigest()
        last = json.loads(STATE.read_text()) if STATE.exists() else {}
        if last.get("sha") == digest:
            print("unchanged: nothing sent")
            return 0
        if a.only_bad and status == "green" and "Regulatory clock" not in msg and last.get("status") in (None, "green"):
            print("all green: nothing sent")
            return 0
        rc = deliver(msg, f"SecuRAX: {status.upper()}", "high" if status == "red" else "default")
        if rc == 0:
            STATE.parent.mkdir(parents=True, exist_ok=True)
            STATE.write_text(json.dumps({"sha": digest, "status": status}))
        return rc
    if a.only_bad and status == "green" and "Regulatory clock" not in msg:
        print("all green: nothing sent")
        return 0
    return deliver(msg, f"SecuRAX: {status.upper()}", "high" if status == "red" else "default")


if __name__ == "__main__":
    sys.exit(main())
