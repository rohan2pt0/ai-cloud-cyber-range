#!/usr/bin/env python3
"""Use SecuRAX from any phone, tablet or computer, like a SaaS app: open your address, sign in with Google, done (doc 85).

    ./securax online setup              once: creates your addresses (hub.<domain>, chat.<domain>), the private tunnel to them and
                                        the sign-in gate, then starts the tunnel. Asks for a Cloudflare API token the first time.
    ./securax online google ID SECRET   sign in with Google (until then Cloudflare e-mails you a one-time code instead)
    ./securax online allow EMAIL        let another of your accounts (or a family member) in
    ./securax online remove EMAIL       take someone off the list (their next sign-in is refused)
    ./securax online status             your addresses, who may sign in, and whether the tunnel is connected
    ./securax online invite             the one line that lets ANOTHER machine serve the same addresses (no single machine needed:
                                        Cloudflare sends each visitor to the nearest machine that is up, and to another when one stops)
    ./securax online join CODE          run that line on the other machine
    ./securax online setup --beta       a separate address for trying new versions (beta-hub.<domain>), so the stable one never changes
    ./securax online off                take the estate offline (the tunnel stops; `online setup` brings it back, nothing is lost)

How it works. Cloudflare Tunnel makes an outbound-only connection from this machine, so no port is opened to the internet.
Cloudflare Access stands in front of every address and lets in only the e-mail addresses you list. The Life OS checks Access's
signed token itself (apps/estate-sync/syncsvc/access.py), so a new device syncs as soon as you sign in, with no link to copy; Chat
signs you in from the same sign-in. The password manager is not put online: the Bitwarden apps cannot pass a sign-in page.

Everything is idempotent: run setup again at any time and it repairs what is missing. Settings go to local/compose/.env (mode 600).
Standard library only; the only network calls are to api.cloudflare.com. Exit codes: 0 done, 1 Cloudflare refused, 2 bad usage.
"""
from __future__ import annotations

import base64
import getpass
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENVF = ROOT / "local" / "compose" / ".env"
API = "https://api.cloudflare.com/client/v4"
POLICY_NAME = "SecuRAX owners"
# what goes online: name -> the service inside the estate (the password manager stays off: the Bitwarden apps cannot sign in to Access)
SERVICES = {"hub": "http://guiding-map:80", "chat": "http://open-webui:8080"}
# what a second machine needs to serve the same addresses (online invite / join); never the Cloudflare API token
JOIN_KEYS = ("CF_TUNNEL_TOKEN", "ONLINE_DOMAIN", "ONLINE_PREFIX", "ONLINE_EMAILS", "SYNC_ACCESS_TEAM", "SYNC_ACCESS_AUD", "SYNC_ACCESS_EMAILS",
             "OWUI_TRUSTED_EMAIL_HEADER", "OIDC_ISSUER", "OIDC_AUDIENCE", "OIDC_JWKS_URL", "AUTH_DEFAULT_ROLES")


def prefix() -> str:
    """'' for the addresses you rely on, 'beta-' for the separate beta ones (online setup --beta)."""
    return "beta-" if env_get("ONLINE_PREFIX") == "beta-" else ""


def hosts(pre: str | None = None) -> dict[str, str]:
    pre = prefix() if pre is None else pre
    return {pre + name: svc for name, svc in SERVICES.items()}


def names(pre: str | None = None) -> tuple[str, str]:
    """(tunnel name, Access application name): the beta ones are separate, so a beta change can never reach the stable addresses."""
    pre = prefix() if pre is None else pre
    return ("securax-beta", "SecuRAX beta") if pre else ("securax", "SecuRAX")
TOKEN_HELP = """A Cloudflare API token lets SecuRAX create the tunnel, the addresses and the sign-in gate for you (about 2 minutes, once):
  1. dash.cloudflare.com > My Profile > API Tokens > Create Token > Create Custom Token.
  2. Permissions (four lines):
       Account | Cloudflare Tunnel | Edit
       Account | Access: Apps and Policies | Edit
       Account | Access: Organizations, Identity Providers, and Groups | Edit
       Zone    | DNS | Edit                     (Zone Resources: Include > Specific zone > {domain})
  3. Continue to summary > Create Token, and paste it below. It is kept in local/compose/.env, readable only by you.
     You can delete it in Cloudflare after setup; SecuRAX then needs a new one only to change who may sign in."""


class Refused(Exception):
    pass


# ---------------------------------------------------------------------------------------------------- .env
def env_get(key: str, default: str = "", path: pathlib.Path | None = None) -> str:
    if os.environ.get(key):
        return os.environ[key]
    try:
        for line in (path or ENVF).read_text("utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return default


def env_set(values: dict[str, str], path: pathlib.Path | None = None) -> None:
    path = path or ENVF
    lines = path.read_text("utf-8").splitlines() if path.exists() else []
    lines = [x for x in lines if x.split("=", 1)[0] not in values] + [f"{k}={v}" for k, v in values.items()]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", "utf-8")
    path.chmod(0o600)


def domain() -> str:
    d = env_get("ONLINE_DOMAIN")
    if not d:
        for line in (ROOT / "brand.env").read_text("utf-8").splitlines():
            if line.startswith("SITE_DOMAIN="):
                d = line.split("=", 1)[1].split(" #")[0].strip().strip("'\"")
    return d


def emails() -> list[str]:
    return [e.strip().lower() for e in env_get("ONLINE_EMAILS").split(",") if e.strip()]


# ---------------------------------------------------------------------------------------------------- Cloudflare API
def make_api(token: str):
    """call(method, path, body) -> result. One function, so the tests can stand in for Cloudflare."""
    def call(method: str, path: str, body=None):
        req = urllib.request.Request(API + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:          # noqa: S310 (fixed https API)
                doc = json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            try:
                doc = json.loads(exc.read() or b"{}")
            except ValueError:
                doc = {}
            msgs = "; ".join(f"{e.get('code')}: {e.get('message')}" for e in doc.get("errors", [])) or str(exc)
            raise Refused(f"{method} {path.split('?')[0]} → {msgs}") from None
        except OSError as exc:
            raise Refused(f"could not reach Cloudflare ({exc})") from None
        if not doc.get("success", True):
            raise Refused(f"{method} {path.split('?')[0]} → " + "; ".join(str(e.get("message")) for e in doc.get("errors", [])))
        return doc.get("result")
    return call


def find_zone(call, dom: str) -> tuple[str, str]:
    z = call("GET", f"/zones?name={dom}") or []
    if not z:
        raise Refused(f"{dom} is not in this Cloudflare account (or the token's DNS permission does not include it)")
    return z[0]["id"], z[0]["account"]["id"]


def team_domain(call, acc: str) -> str:
    try:
        org = call("GET", f"/accounts/{acc}/access/organizations") or {}
    except Refused as exc:
        raise Refused("Zero Trust is not switched on yet: open one.dash.cloudflare.com once, choose a team name and the Free plan, "
                      f"then run this again ({exc})") from None
    if not org.get("auth_domain"):
        raise Refused("Zero Trust has no team name yet: one.dash.cloudflare.com > Settings > Team name, then run this again")
    return org["auth_domain"]


def ensure_tunnel(call, acc: str, dom: str) -> tuple[str, str]:
    tname = names()[0]
    found = call("GET", f"/accounts/{acc}/cfd_tunnel?name={tname}&is_deleted=false") or []
    tid = found[0]["id"] if found else call("POST", f"/accounts/{acc}/cfd_tunnel", {"name": tname, "config_src": "cloudflare"})["id"]
    ingress = [{"hostname": f"{h}.{dom}", "service": svc, "originRequest": {}} for h, svc in hosts().items()] + [{"service": "http_status:404"}]
    call("PUT", f"/accounts/{acc}/cfd_tunnel/{tid}/configurations", {"config": {"ingress": ingress}})
    token = call("GET", f"/accounts/{acc}/cfd_tunnel/{tid}/token")
    return tid, token


def ensure_dns(call, zone: str, dom: str, tid: str) -> None:
    target = f"{tid}.cfargotunnel.com"
    for h in hosts():
        name = f"{h}.{dom}"
        rec = {"type": "CNAME", "name": name, "content": target, "proxied": True, "comment": "SecuRAX online (./securax online)"}
        have = call("GET", f"/zones/{zone}/dns_records?name={name}") or []
        if not have:
            call("POST", f"/zones/{zone}/dns_records", rec)
        elif have[0].get("content") != target or have[0].get("type") != "CNAME" or not have[0].get("proxied"):
            if have[0].get("type") != "CNAME":
                raise Refused(f"{name} already exists as a {have[0].get('type')} record: rename it or set ONLINE_DOMAIN to another domain")
            call("PUT", f"/zones/{zone}/dns_records/{have[0]['id']}", rec)


def ensure_idps(call, acc: str) -> list[dict]:
    """The one-time e-mail code always (it needs no setup, and it is your way in if Google ever locks you out), plus Google once you
    added it (online google). Two ways in, so no single sign-in provider can lock you out of your own estate."""
    idps = call("GET", f"/accounts/{acc}/access/identity_providers") or []
    otp = [i for i in idps if i.get("type") == "onetimepin"]
    otp = otp[0] if otp else call("POST", f"/accounts/{acc}/access/identity_providers", {"name": "E-mail code", "type": "onetimepin", "config": {}})
    return [i for i in idps if i.get("type") == "google"][:1] + [otp]


def ensure_policy(call, acc: str, who: list[str]) -> str:
    body = {"name": POLICY_NAME, "decision": "allow", "include": [{"email": {"email": e}} for e in who]}
    have = [p for p in (call("GET", f"/accounts/{acc}/access/policies") or []) if p.get("name") == POLICY_NAME]
    if have:
        call("PUT", f"/accounts/{acc}/access/policies/{have[0]['id']}", body)
        return have[0]["id"]
    return call("POST", f"/accounts/{acc}/access/policies", body)["id"]


def ensure_app(call, acc: str, dom: str, policy: str, idps: list[dict]) -> dict:
    hs, app_name = [f"{h}.{dom}" for h in hosts()], names()[1]
    body = {"name": app_name, "type": "self_hosted", "domain": hs[0], "destinations": [{"type": "public", "uri": h} for h in hs],
            "policies": [{"id": policy, "precedence": 1}], "allowed_idps": [i["id"] for i in idps], "auto_redirect_to_identity": len(idps) == 1,
            "session_duration": env_get("ONLINE_SESSION", "720h"), "app_launcher_visible": False}
    have = [a for a in (call("GET", f"/accounts/{acc}/access/apps") or []) if a.get("domain") == hs[0] or a.get("name") == app_name]
    return call("PUT", f"/accounts/{acc}/access/apps/{have[0]['id']}", body) if have else call("POST", f"/accounts/{acc}/access/apps", body)


def setup(call, dom: str, who: list[str], say=print) -> dict[str, str]:
    """Everything Cloudflare needs, made or repaired; returns the settings for .env."""
    zone, acc = find_zone(call, dom)
    say(f"  ✔ {dom} found in your Cloudflare account")
    team = team_domain(call, acc)
    tid, tok = ensure_tunnel(call, acc, dom)
    say("  ✔ private tunnel ready (outbound only: no port opened on this machine)")
    ensure_dns(call, zone, dom, tid)
    say("  ✔ addresses: " + ", ".join(f"https://{h}.{dom}" for h in hosts()))
    idps = ensure_idps(call, acc)
    pol = ensure_policy(call, acc, who)
    app = ensure_app(call, acc, dom, pol, idps)
    by = "Google, or a one-time code e-mailed to you" if len(idps) > 1 else "a one-time code e-mailed to you (Google: ./securax online google)"
    say(f"  ✔ sign-in gate: only {', '.join(who)}, by {by}")
    return {"CF_TUNNEL_TOKEN": tok, "CF_ACCOUNT_ID": acc, "ONLINE_DOMAIN": dom, "ONLINE_PREFIX": prefix(), "ONLINE_EMAILS": ",".join(who),
            "SYNC_ACCESS_TEAM": team, "SYNC_ACCESS_AUD": str(app.get("aud", "")), "SYNC_ACCESS_EMAILS": ",".join(who),
            "OWUI_TRUSTED_EMAIL_HEADER": "Cf-Access-Authenticated-User-Email", "BIND_HOST": "127.0.0.1",
            # the AI gateway can know who each signed-in person is (their own allowance, no API key of theirs needed). Inert until
            # `./securax gateway-auth enable`, which also gives Chat and the CLI their own service keys (doc 86).
            "OIDC_ISSUER": f"https://{team}", "OIDC_AUDIENCE": str(app.get("aud", "")), "OIDC_JWKS_URL": f"https://{team}/cdn-cgi/access/certs",
            "AUTH_DEFAULT_ROLES": "user"}


def add_google(call, acc: str, client_id: str, secret: str) -> None:
    have = [i for i in (call("GET", f"/accounts/{acc}/access/identity_providers") or []) if i.get("type") == "google"]
    body = {"name": "Google", "type": "google", "config": {"client_id": client_id, "client_secret": secret}}
    if have:
        call("PUT", f"/accounts/{acc}/access/identity_providers/{have[0]['id']}", body)
    else:
        call("POST", f"/accounts/{acc}/access/identity_providers", body)


# ---------------------------------------------------------------------------------------------------- CLI
def _optional(add: bool) -> None:
    cur = env_get("SECURAX_OPTIONAL").split()
    cur = [x for x in cur if x != "online"] + (["online"] if add else [])
    env_set({"SECURAX_OPTIONAL": " ".join(cur)})


def _token(say) -> str:
    tok = env_get("CF_API_TOKEN")
    if tok:
        return tok
    say(TOKEN_HELP.format(domain=domain()))
    tok = getpass.getpass("\nCloudflare API token (hidden as you paste): ").strip()
    if not re.fullmatch(r"[A-Za-z0-9_\-]{30,}", tok):
        raise Refused("that does not look like a Cloudflare API token")
    env_set({"CF_API_TOKEN": tok})
    return tok


def _ask_emails(say) -> list[str]:
    who = emails()
    if who:
        return who
    e = input("Your e-mail address for signing in (your Google account, if you will use Google): ").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e):
        raise Refused("that is not an e-mail address")
    return [e]


def main(argv: list[str] | None = None, say=print) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "status"
    try:
        if cmd == "setup":
            if "--beta" in argv[1:]:
                env_set({"ONLINE_PREFIX": "beta-"})
            dom = domain()
            if not dom:
                say("No domain: set ONLINE_DOMAIN=your-domain in local/compose/.env (it must be in your Cloudflare account).")
                return 2
            if env_get("BIND_HOST", "127.0.0.1") not in ("127.0.0.1", "localhost"):
                say("  note: BIND_HOST was " + env_get("BIND_HOST") + "; online mode sets it back to 127.0.0.1, because Chat now trusts the")
                say("  sign-in header and must be reachable only through the tunnel. Phones use your new addresses instead.")
            say(f"SecuRAX online · {dom}")
            values = setup(make_api(_token(say)), dom, _ask_emails(say), say)
            env_set(values)
            _optional(True)
            say(f"\nStarting the tunnel with the estate. Then, on any device: open https://{prefix()}hub.{dom} and sign in.")
            say("  Install it: Share > Add to Home Screen (iPhone), or the browser's Install app (Android, Windows, Mac).")
            return 0
        if cmd == "google" and len(argv) == 3:
            acc = env_get("CF_ACCOUNT_ID")
            if not acc:
                say("Run  ./securax online setup  first.")
                return 2
            add_google(make_api(_token(say)), acc, argv[1], argv[2])
            say("✔ Google sign-in added. Running setup again so your addresses use it...")
            return main(["setup"], say)
        if cmd == "allow" and len(argv) == 2:
            e = argv[1].strip().lower()
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e):
                say("That is not an e-mail address.")
                return 2
            env_set({"ONLINE_EMAILS": ",".join(dict.fromkeys(emails() + [e]))})
            return main(["setup"], say)
        if cmd == "remove" and len(argv) == 2:
            e, left = argv[1].strip().lower(), [x for x in emails() if x != argv[1].strip().lower()]
            if not left:
                say("That would leave nobody able to sign in. Add the new address first:  ./securax online allow EMAIL")
                return 2
            if e not in emails():
                say(f"{e} is not on the list (" + ", ".join(emails()) + ").")
                return 2
            env_set({"ONLINE_EMAILS": ",".join(left)})
            return main(["setup"], say)
        if cmd == "invite":
            if not env_get("CF_TUNNEL_TOKEN"):
                say("This machine is not online yet: ./securax online setup")
                return 2
            code = base64.urlsafe_b64encode(json.dumps({k: env_get(k) for k in JOIN_KEYS}).encode()).decode().rstrip("=")
            say("On the OTHER machine (its estate already installed), run this. Treat it like a password: it lets that machine serve")
            say("your addresses. Send it over SSH or your password manager, never in a chat or e-mail.\n")
            say(f"  ./securax online join {code}\n")
            say("Also sync the data between the two:  ./securax nodes invite  (doc 86).")
            return 0
        if cmd == "join" and len(argv) == 2:
            try:
                got = json.loads(base64.urlsafe_b64decode(argv[1] + "=" * (-len(argv[1]) % 4)))
                assert isinstance(got, dict) and got.get("CF_TUNNEL_TOKEN") and got.get("ONLINE_DOMAIN")
            except (ValueError, AssertionError):
                say("That is not a join line from  ./securax online invite  (copy the whole line).")
                return 2
            env_set({**{k: str(got.get(k, "")) for k in JOIN_KEYS}, "BIND_HOST": "127.0.0.1"})
            _optional(True)
            say(f"✔ this machine now serves https://{prefix()}hub.{got['ONLINE_DOMAIN']} too. Starting the estate with the tunnel…")
            return 0
        if cmd == "off":
            _optional(False)
            subprocess.run(["docker", "compose", "--profile", "online", "stop", "cloudflared"], cwd=ROOT / "local" / "compose",
                           capture_output=True)
            say("✔ offline: the tunnel is stopped (your addresses show a Cloudflare error page). Back online:  ./securax online setup")
            return 0
        if cmd == "status":
            dom, on = env_get("ONLINE_DOMAIN"), "online" in env_get("SECURAX_OPTIONAL").split()
            if not env_get("CF_TUNNEL_TOKEN"):
                say("Not online yet. One command puts SecuRAX on your own addresses, behind your sign-in:  ./securax online setup")
                return 0
            r = subprocess.run(["docker", "ps", "--filter", "label=com.docker.compose.service=cloudflared", "--format", "{{.Status}}"],
                               capture_output=True, text=True)
            running = r.returncode == 0 and r.stdout.strip().startswith("Up")
            say(f"{'✔' if on and running else '✗'} online: {'tunnel connected' if running else 'tunnel NOT running (./securax up)'}" + ("" if on else " · switched off"))
            for h in hosts():
                say(f"  https://{h}.{dom}")
            say("  who may sign in: " + ", ".join(emails()))
            return 0 if on and running else 1
    except Refused as exc:
        say(f"✗ Cloudflare refused: {exc}")
        say("  SecuRAX was not switched online. Fix the cause above and run the same command again: it reuses what was already made.")
        return 1
    except (EOFError, KeyboardInterrupt):
        say("\nStopped; nothing changed.")
        return 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
