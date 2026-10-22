#!/usr/bin/env python3
"""Encryption in transit for the whole estate: one private certificate authority, one TLS edge, addresses by NAME, no plain-HTTP web ports.

    ./securax tls on [--domain securax.example.in] [--hosts 100.x.y.z]   create the CA + certificate, switch the HTTPS edge on (then: ./securax down && ./securax up)
    ./securax tls trust [--apply]                   make THIS computer's browsers trust the CA (Windows/WSL, macOS, Linux)
    ./securax tls status [--json]                   certificate expiry, which names resolve, which HTTPS names answer, which plain ports are still open
    ./securax tls render                            (re)write the edge configuration for the current domain (done automatically by `on` and `up`)
    ./securax tls renew                             re-issue the server certificate (same CA; nothing to re-trust)
    ./securax tls off                               back to plain HTTP (the estate still works; browsers show 'not secure')
    ./securax tls internal on|off                   ALSO encrypt the hops between the services themselves (needs `tls on` first; see docs/securax/40)

What it builds (no new image, no new dependency; uses the nginx image the estate already runs, and the `openssl` that ships with Linux/WSL):
  * a private CA (ECDSA P-256) whose key never leaves ~/.securax/tls (mode 600) and that is NAME-CONSTRAINED: even if its key leaked it could
    only vouch for localhost, private/Tailscale addresses, *.securax.internal and the one domain you chose - never for a real website.
    Trusting it is therefore low-risk.
  * a server certificate (397 days, ECDSA P-256) for the domain (wildcard) and the addresses you use, kept in the same folder.
  * `tls-edge` (nginx): TLS 1.2/1.3 only, forward-secret ciphers, no session tickets, ONE published port (443) that routes by NAME:
    hub.<domain>  chat.<domain>  docs.<domain>  flows.<domain>  sync.<domain>  api.<domain>
    No port number ever appears in an address, so a moved service, a new IP or a second machine changes one DNS entry, not every
    bookmark, app setting and phone. With TLS on, the services' plain HTTP ports are NOT published on the host at all.
  * the default domain `securax.localhost` needs no DNS (browsers resolve *.localhost to this machine). For other devices use a domain
    you control (`--domain securax.example.in`) with ONE wildcard DNS record (*.securax.example.in) pointing at the machine's private or
    Tailscale address: that record is the only place an IP address lives.
Honest limits: this encrypts everything that reaches a browser, a phone or another machine. Traffic BETWEEN containers on the private Docker
networks is covered by phase 2 (docs/securax/40) and is listed by `tls status` until it is. The CA key is only as safe as this account.
"""
from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import os
import pathlib
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "local" / "compose"
ENVF = COMPOSE / ".env"
EDGE_CONF = COMPOSE / "tls-edge.generated.conf"
DAYS_SERVER = 397                 # browsers/OSes refuse longer-lived certificates from some CAs; renewing yearly is the norm
DAYS_CA = 3650
RENEW_WITHIN_DAYS = 30
PERMITTED_DNS = ["localhost", "securax.internal", ".ts.net", ".local"]
PERMITTED_NETS = ["127.0.0.0/8", "::1/128", "100.64.0.0/10", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]   # loopback, Tailscale, private LAN
DEFAULT_DOMAIN = "securax.localhost"
# (label, name, upstream service, upstream port, plain port it replaces)  -  the edge configuration is generated from this one table
ENDPOINTS = [
    ("Command Center / Guiding Map", "hub", "guiding-map", 80, 8088),
    ("Chat", "chat", "open-webui", 8080, 3000),
    ("Private Docs", "docs", "anythingllm", 3001, 3001),
    ("Automation (n8n)", "flows", "n8n", 5678, 5678),
    ("Password manager", "pass", "vaultwarden", 80, 8222),
    ("Sync service (phone/PWA)", "sync", "estate-sync", 8089, 8089),
    ("Gateway API", "api", "gateway", 8080, 8080),
]
PLAIN_WEB_PORTS = (8088, 3000, 3001, 5678, 8089, 8222)          # published only while the edge is OFF
TLS_COMPOSE = "docker-compose.yml:tls.yml"
TLS_COMPOSE_INTERNAL = "docker-compose.yml:tls.yml:tls-internal.yml"
SIDECAR_DIR = COMPOSE / "tls-sidecars"
SIDECAR_PORT = 8443
# Internal hops (phase 2): one nginx sidecar per service sharing that service's network namespace. It terminates TLS on 8443 with a certificate of
# its own (<name>.securax.internal) and forwards to the service on 127.0.0.1, where the service now listens ONLY (so its plain port is unreachable from
# any other container). (service, upstream port inside the container, can its image be told to listen on loopback only?)
INTERNAL = [
    ("gateway", 8080, True), ("litellm", 4000, True), ("ollama", 11434, True), ("open-webui", 8080, True),
    ("n8n", 5678, True), ("estate-sync", 8089, True), ("anythingllm", 3001, False),
]
INTERNAL_EXCEPTIONS = ["Private Docs (AnythingLLM) cannot be told to listen on loopback only, so its plain port stays reachable from other containers on the private Docker network (its TLS sidecar protects the edge hop only)"]

# Hops that stay on the private Docker networks (never leave this machine) and are NOT yet encrypted. Listed on purpose: an unmentioned
# plaintext hop is how an audit finding is born. Phase 2 (docs/securax/40) closes them.
INTERNAL_HOPS = [
    "Chat / n8n -> gateway", "gateway -> model router (LiteLLM)", "router -> local model (Ollama)", "Private Docs -> local model (Ollama)",
    "edge -> each service (the last hop inside this machine)",
]   # (no service uses Postgres, so there is no database hop to encrypt)


def tls_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_TLS_DIR") or pathlib.Path.home() / ".securax" / "tls")


def run(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, text=True, capture_output=True, **kw)


def need_openssl() -> str:
    exe = shutil.which("openssl")
    if not exe:
        raise SystemExit("openssl is needed (Ubuntu/WSL:  sudo apt-get install -y openssl)")
    return exe


def write_private(path: pathlib.Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(data)
    os.chmod(path, 0o600)


# ───────────────────────────────────────────── domain ─────────────────────────────────────────────
def valid_domain(d: str) -> bool:
    return bool(re.fullmatch(r"(?=.{4,200}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", d.lower()))


def domain() -> str:
    d = (os.environ.get("SECURAX_DOMAIN") or read_env().get("SECURAX_DOMAIN") or DEFAULT_DOMAIN).strip().lower()
    return d if valid_domain(d) else DEFAULT_DOMAIN


def host_of(name: str, dom: str | None = None) -> str:
    return f"{name}.{dom or domain()}"


# ───────────────────────────────────────────── names ─────────────────────────────────────────────
def is_ip(s: str) -> bool:
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


def canon(name: str) -> str:
    """One spelling per name (openssl prints ::1 as 0:0:0:0:0:0:0:1; a wildcard keeps its '*.'), so 'already covered' is judged correctly."""
    if name.startswith("*."):
        return "*." + name[2:].lower()
    return str(ipaddress.ip_address(name)) if is_ip(name) else name.lower()


def ca_domains(d: pathlib.Path) -> list[str]:
    """Extra domains this CA was created to vouch for (recorded when the CA was made; the constraint inside ca.crt is what is enforced)."""
    try:
        return json.loads((d / "ca.names.json").read_text("utf-8")).get("domains", [])
    except (OSError, ValueError):
        return []


def permitted(name: str, hostname: str | None = None, extra: list[str] | None = None) -> bool:
    """Would the CA's name constraints allow this name? (so we refuse early instead of making a certificate browsers reject)"""
    if is_ip(name):
        ip = ipaddress.ip_address(name)
        return any(ip.version == ipaddress.ip_network(n).version and ip in ipaddress.ip_network(n) for n in PERMITTED_NETS)
    low = name.lower().removeprefix("*.")
    if hostname and low == hostname.lower():
        return True
    for p in PERMITTED_DNS + [e.lower() for e in (extra or [])]:
        if p.startswith("."):
            if low.endswith(p):
                return True
        elif low == p or low.endswith("." + p):
            return True
    return False


def local_names(dom: str, extra: list[str] | None = None) -> list[str]:
    """Every name/address the certificate must cover: the domain (wildcard), loopback, this machine, Tailscale, anything you add."""
    names = [dom, "*." + dom, "localhost", "127.0.0.1", "::1"]
    host = socket.gethostname()
    if host and host not in names:
        names.append(host)
    ts = run(["tailscale", "ip", "-4"]) if shutil.which("tailscale") else None
    if ts and ts.returncode == 0:
        names += [ln.strip() for ln in ts.stdout.splitlines() if ln.strip()]
    bind = read_env().get("BIND_HOST", "")
    if bind and bind not in ("0.0.0.0", "127.0.0.1", ""):
        names.append(bind)
    names += [n.strip() for n in (extra or []) if n.strip()]
    names += [n.strip() for n in read_env().get("TLS_EXTRA_NAMES", "").split(",") if n.strip()]
    seen, out = set(), []
    for n in names:
        if canon(n) not in seen:
            seen.add(canon(n))
            out.append(n)
    return out


def san_line(names: list[str]) -> str:
    return ",".join(("IP:" if is_ip(n) else "DNS:") + n for n in names)


# ───────────────────────────────────────────── issuing ─────────────────────────────────────────────
def constraints(hostnames: list[str], domains: list[str]) -> str:
    dns = list(dict.fromkeys(PERMITTED_DNS + [d.lower() for d in domains] + [h.lower() for h in hostnames if h and not is_ip(h)]))
    ips = []
    for n in PERMITTED_NETS:
        net = ipaddress.ip_network(n)
        ips.append(f"{net.network_address}/{net.netmask}")
    return "critical," + ",".join([f"permitted;DNS:{d}" for d in dns] + [f"permitted;IP:{i}" for i in ips])


def make_ca(d: pathlib.Path, hostnames: list[str], domains: list[str]) -> None:
    exe = need_openssl()
    d.mkdir(parents=True, exist_ok=True)
    os.chmod(d, 0o700)
    key = d / "ca.key"
    r = run([exe, "ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", str(key)])
    if r.returncode:
        raise SystemExit("openssl could not create the CA key:\n" + r.stderr)
    os.chmod(key, 0o600)
    r = run([exe, "req", "-x509", "-new", "-key", str(key), "-sha256", "-days", str(DAYS_CA), "-out", str(d / "ca.crt"),
             "-subj", f"/O=SecuRAX/CN=SecuRAX Local CA ({socket.gethostname()})",
             "-addext", "basicConstraints=critical,CA:TRUE,pathlen:0",
             "-addext", "keyUsage=critical,keyCertSign,cRLSign",
             "-addext", "nameConstraints=" + constraints(hostnames, domains)])
    if r.returncode:
        raise SystemExit("openssl could not create the CA certificate:\n" + r.stderr)
    write_private(d / "ca.names.json", json.dumps({"domains": domains, "hostnames": hostnames}))


def issue_server(d: pathlib.Path, names: list[str]) -> None:
    exe = need_openssl()
    with tempfile.TemporaryDirectory() as t:
        ext = pathlib.Path(t) / "ext.cnf"
        ext.write_text("basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\n"
                       "extendedKeyUsage=serverAuth\nsubjectAltName=" + san_line(names) + "\n")
        csr = pathlib.Path(t) / "s.csr"
        key = d / "server.key"
        r = run([exe, "req", "-new", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes",
                 "-keyout", str(key), "-out", str(csr), "-subj", "/CN=localhost"])
        if r.returncode:
            raise SystemExit("openssl could not create the server key:\n" + r.stderr)
        os.chmod(key, 0o600)
        r = run([exe, "x509", "-req", "-in", str(csr), "-CA", str(d / "ca.crt"), "-CAkey", str(d / "ca.key"), "-CAcreateserial",
                 "-days", str(DAYS_SERVER), "-sha256", "-extfile", str(ext), "-out", str(d / "server.crt")])
        if r.returncode:
            raise SystemExit("openssl could not sign the server certificate:\n" + r.stderr)
    (d / "ca.srl").unlink(missing_ok=True)
    os.chmod(d / "server.crt", 0o644)


def cert_info(path: pathlib.Path) -> dict:
    """Expiry and names of a certificate, read with openssl (no parsing library needed)."""
    exe = shutil.which("openssl")
    if not exe or not path.exists():
        return {}
    r = run([exe, "x509", "-in", str(path), "-noout", "-enddate", "-ext", "subjectAltName"])
    if r.returncode:
        return {}
    m = re.search(r"notAfter=(.*)", r.stdout)
    end = dt.datetime.strptime(m.group(1).strip(), "%b %d %H:%M:%S %Y %Z").replace(tzinfo=dt.timezone.utc) if m else None
    sans = re.findall(r"(?:DNS|IP Address):([^,\s]+)", r.stdout)
    return {"expires": end.isoformat() if end else None,
            "days_left": (end - dt.datetime.now(dt.timezone.utc)).days if end else None, "names": sans}


def plan_names(extra: list[str] | None, dom: str, ca_extra: list[str]) -> tuple[list[str], list[str]]:
    ok, bad = [], []
    host = socket.gethostname()
    for n in local_names(dom, extra):
        (ok if permitted(n, host, ca_extra) else bad).append(n)
    return ok, bad


def ensure(extra: list[str] | None = None, force: bool = False, dom: str | None = None, new_ca: bool = False) -> dict:
    d = tls_dir()
    dom = dom or domain()
    host = socket.gethostname()
    have_ca = (d / "ca.crt").exists() and (d / "ca.key").exists()
    covered_by_ca = ca_domains(d)
    needs_domain = dom != DEFAULT_DOMAIN and not permitted(dom, host, covered_by_ca)
    if have_ca and needs_domain and not new_ca:
        raise SystemExit(f"The existing authority cannot vouch for '{dom}' (it was created for: localhost, private addresses"
                         + (f", {', '.join(covered_by_ca)}" if covered_by_ca else "") + ").\n"
                         f"  Create a new one with:  ./securax tls on --domain {dom} --new-ca\n"
                         "  It must be trusted again on every device (./securax tls trust). Remove the old one from your browsers afterwards.")
    if new_ca or not have_ca:
        make_ca(d, [host, host.lower()], [] if dom == DEFAULT_DOMAIN else [dom])
        force = True
        covered_by_ca = ca_domains(d)
    names, refused = plan_names(extra, dom, covered_by_ca)
    info = cert_info(d / "server.crt")
    have = {canon(n) for n in info.get("names", [])}
    missing = [n for n in names if canon(n) not in have]
    if force or not info or missing or (info.get("days_left") or 0) < RENEW_WITHIN_DAYS:
        issue_server(d, names)
        info = cert_info(d / "server.crt")
    return {"dir": str(d), "names": names, "refused": refused, "cert": info, "domain": dom}


# ───────────────────────────────────────────── edge configuration ─────────────────────────────────────────────
EDGE_HEAD = """# TLS edge for the whole estate - GENERATED by `./securax tls render` from governance/tls.py (do not edit; docs/securax/40).
# One nginx, one certificate, modern TLS only, ONE port (443) that routes by NAME. Every browser-facing service is reached through here
# and its plain-HTTP port is NOT published on the host while the edge is on (see tls.yml).
# Upstream names are resolved lazily (resolver + variable), so a service that is not running (Private Docs, n8n on a small machine)
# cannot stop the edge from starting.
#
# NOT set on purpose: HSTS. Browsers key it on the HOST NAME, so it would pin the whole domain for the policy lifetime and break
# unrelated local tools the day you switch the edge off.

resolver 127.0.0.11 valid=10s ipv6=off;

map $http_upgrade $connection_upgrade { default upgrade; '' close; }

ssl_certificate     /etc/tls/server.crt;
ssl_certificate_key /etc/tls/server.key;
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
# Post-quantum: hybrid X25519+ML-KEM-768 key exchange first (needs OpenSSL >= 3.5, i.e. nginx >= 1.30 images; Chrome/Edge/Firefox offer it by default),
# classical curves after it for clients that do not. An older OpenSSL would REFUSE to start with this line, so the image tag is pinned with it.
ssl_ecdh_curve X25519MLKEM768:X25519:prime256v1:secp384r1;
ssl_session_tickets off;            # keeps forward secrecy: no long-lived ticket key
ssl_session_cache shared:SSL:2m;
ssl_session_timeout 10m;
server_tokens off;

# headers every upstream gets (WebSockets for Chat/n8n/sync, streaming answers, long model replies, large uploads)
proxy_http_version 1.1;
proxy_set_header Host $http_host;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header X-Forwarded-For $remote_addr;   # overwritten with the address the edge saw, never appended to the client's own
proxy_set_header X-Real-IP $remote_addr;         # the same, for services that count per client (estate-sync's refused sign-ins, doc 87)
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;
proxy_buffering off;                # server-sent events: tokens must reach the browser as they are produced
proxy_read_timeout 600s;
proxy_send_timeout 600s;
client_max_body_size 100m;

# plain HTTP on port 80 only ever redirects (it serves nothing)
server {
    listen 80 default_server;
    server_name _;
    return 301 https://$host$request_uri;
}

# an unknown name (or a raw IP address) gets the certificate handshake but NO service
server {
    listen 443 ssl default_server;
    http2 on;
    server_name _;
    return 421;
}
"""


# services that are OPTIONAL (skipped in lite mode) -> what to type to start them. Used for the friendly "not running" page.
OPTIONAL = {"docs": ("Private Docs", "docs"), "flows": ("Automation (n8n)", "flows"), "pass": ("Password manager", "passwords")}


def _upstream(svc: str, port: int, internal: bool) -> tuple[str, str]:
    if internal and svc in {n for n, _p, _l in INTERNAL}:
        return f"https://{svc}.securax.internal:{SIDECAR_PORT}", f"    proxy_ssl_name {svc}.securax.internal;\n"
    return f"http://{svc}:{port}", ""


def _probes(internal: bool) -> str:
    """Same-origin status probes for the Command Center: /_up/<name> proxies to that service and returns ITS status (502 = not running).
    A browser's cross-origin no-cors fetch cannot read a status, so a stopped service used to be shown as running."""
    out = []
    for _label, name, svc, port, _plain in ENDPOINTS:
        if name == "hub":
            continue
        up, extra = _upstream(svc, port, internal)
        out.append(f"    location = /_up/{name} {{\n        set $pu {up};\n{extra}        rewrite ^ / break;\n        proxy_pass $pu;\n    }}\n")
    return "".join(out)


def _down_page(label: str, name: str) -> str:
    """What a person sees when a service is not running: a sentence and the exact command, not a bare nginx 502."""
    cmd = f"./securax start {OPTIONAL[name][1]}" if name in OPTIONAL else "./securax up"
    why = ("It is optional and is skipped on smaller machines (lite mode)." if name in OPTIONAL else "It is not responding (it may still be starting).")
    body = (f"<!doctype html><meta charset=utf-8><title>{label} is not running</title>"
            f"<body style=\"font:16px system-ui;max-width:40em;margin:4em auto;padding:0 1em\"><h1>{label} is not running</h1>"
            f"<p>{why}</p><p>Start it, then reload this page:</p><pre>{cmd}</pre>"
            f"<p><a href=\"https://hub.{{dom}}/hub.html\">Back to the Command Center</a></p>")
    return body


# Device ports (doc 58): your phones reach the estate through `tailscale serve`, which forwards to a PORT, not a name. These two
# loopback-only ports let it do that while the edge keeps the professional names on this machine (https://hub.<domain>):
#   127.0.0.1:9443 -> the app, with /v1, /healthz, /version and /sync on the same origin     127.0.0.1:9444 -> Chat
# They answer whatever host name arrives (the phone sees https://<laptop>.<tailnet>.ts.net, with Tailscale's own certificate).
DEVICE_PORTS = {"hub": 9443, "chat": 9444}


def render_device_ports(internal: bool = False) -> str:
    up = {name: _upstream(svc, port, internal) for _l, name, svc, port, _p in ENDPOINTS}
    hub_up, hub_extra = up["hub"] if not internal else ("", "")
    root = ("    root /usr/share/nginx/html;\n    index index.html;\n    location / { try_files $uri $uri/ /index.html; }\n"
            "    location /portal/ { alias /srv/portal/; index index.html; }\n" if internal
            else f"    set $up {hub_up};\n{hub_extra}    location / {{ proxy_pass $up; }}\n")
    same_origin = ""
    for path, name in (("/v1/", "api"), ("= /healthz", "api"), ("= /version", "api"), ("/sync", "sync")):
        u, extra = up[name]
        same_origin += f"    location {path} {{\n        set $so {u};\n{extra.replace('    ', '        ')}        proxy_pass $so;\n    }}\n"
    chat_up, chat_extra = up["chat"]
    return f"""
# Device port: the app for phones over Tailscale (tailscale serve -> https+insecure://127.0.0.1:{DEVICE_PORTS['hub']})
server {{
    listen {DEVICE_PORTS['hub']} ssl;
    http2 on;
    server_name _;
    add_header Cache-Control "no-cache" always;
{root}{same_origin}}}

# Device port: Chat for phones over Tailscale (tailscale serve --https=10000 -> https+insecure://127.0.0.1:{DEVICE_PORTS['chat']})
server {{
    listen {DEVICE_PORTS['chat']} ssl;
    http2 on;
    server_name _;
    set $up {chat_up};
{chat_extra}    location / {{ proxy_pass $up; }}
}}
"""


def render_edge_conf(dom: str | None = None, internal: bool = False) -> str:
    dom = dom or domain()
    out = [EDGE_HEAD]
    if internal:
        out.append("""
# Internal TLS is ON: the edge talks to every service over HTTPS too and VERIFIES it against the estate's own CA.
proxy_ssl_verify on;
proxy_ssl_trusted_certificate /etc/tls/ca.crt;
proxy_ssl_server_name on;
proxy_ssl_protocols TLSv1.2 TLSv1.3;
""")
    for label, name, svc, port, _plain in ENDPOINTS:
        if svc == "guiding-map" and internal:
            out.append(f"""
# {label}: served by the edge itself (static files), so there is no hop to encrypt
server {{
    listen 443 ssl;
    http2 on;
    server_name {name}.{dom};
    root /usr/share/nginx/html;
    index index.html;
    add_header Cache-Control "no-cache" always;
{_probes(internal)}    location / {{ try_files $uri $uri/ /index.html; }}
    location = /hub           {{ return 302 /hub.html; }}
    location = /apps          {{ return 302 /hub.html; }}
    location = /portal/hub.html {{ return 302 /hub.html; }}
    location /portal/ {{ alias /srv/portal/; index index.html; }}
}}
""")
            continue
        up, extra = _upstream(svc, port, internal)
        names = f"{name}.{dom}" + (" localhost 127.0.0.1" if (internal and svc == "gateway") else "")
        probes = _probes(internal) if name == "hub" else ""
        down = ""
        if name != "hub" and name != "api":
            page = _down_page(label, name).replace("{dom}", dom)
            down = f"    error_page 502 503 504 /_down;\n    location = /_down {{ internal; default_type text/html; return 502 '{page}'; }}\n"
        out.append(f"""
# {label}
server {{
    listen 443 ssl;
    http2 on;
    server_name {names};
    set $up {up};
{extra}{probes}{down}    location / {{ proxy_pass $up; }}
}}
""")
    out.append(render_device_ports(internal))
    return "".join(out)


def sidecar_conf(svc: str, port: int) -> str:
    """The TLS sidecar of one service: terminate TLS with the service's own certificate, forward to the service on loopback."""
    return f"""# TLS sidecar for {svc} - GENERATED by `./securax tls render` (do not edit; docs/securax/40).
map $http_upgrade $connection_upgrade {{ default upgrade; '' close; }}
server {{
    listen {SIDECAR_PORT} ssl;
    server_name {svc}.securax.internal;
    ssl_certificate     /etc/tls/{svc}.crt;
    ssl_certificate_key /etc/tls/{svc}.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-CHACHA20-POLY1305;
    ssl_ecdh_curve X25519MLKEM768:X25519:prime256v1:secp384r1;
    ssl_session_tickets off;
    server_tokens off;
    client_max_body_size 100m;
    # The client's address: only a caller on the private Docker networks (the edge) may name it in X-Real-IP; anyone else is
    # counted as itself. Then it is passed on OVERWRITTEN, never appended to a header the caller sent.
    set_real_ip_from 172.16.0.0/12;
    real_ip_header X-Real-IP;
    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_buffering off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }}
}}
"""


def write_edge_conf(dom: str | None = None) -> pathlib.Path:
    EDGE_CONF.write_text(render_edge_conf(dom, internal=tls_internal_on()), "utf-8")
    if tls_internal_on():
        SIDECAR_DIR.mkdir(exist_ok=True)
        for svc, port, _loop in INTERNAL:
            (SIDECAR_DIR / f"{svc}.conf").write_text(sidecar_conf(svc, port), "utf-8")
    return EDGE_CONF


# ───────────────────────────────────────────── env + compose ─────────────────────────────────────────────
def read_env() -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for ln in ENVF.read_text("utf-8").splitlines():
            if ln.strip() and not ln.lstrip().startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def set_env(key: str, value: str | None) -> None:
    lines = ENVF.read_text("utf-8").splitlines() if ENVF.exists() else []
    lines = [ln for ln in lines if not ln.startswith(key + "=")]
    if value is not None:
        lines.append(f"{key}={value}")
    write_private(ENVF, "\n".join(lines) + "\n")


def tls_is_on() -> bool:
    return "tls.yml" in read_env().get("COMPOSE_FILE", "")


def tls_internal_on() -> bool:
    return tls_is_on() and read_env().get("TLS_INTERNAL") == "1"


def system_ca_bundle() -> str:
    """The operating system's trusted public CAs (so a client that gets OUR CA added still trusts api.openai.com etc.)."""
    for cand in (ssl.get_default_verify_paths().cafile, "/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt", "/etc/ssl/cert.pem"):
        if cand and pathlib.Path(cand).exists():
            return pathlib.Path(cand).read_text("utf-8", "replace")
    try:
        import certifi
        return pathlib.Path(certifi.where()).read_text("utf-8")
    except ImportError:
        raise SystemExit("no public CA bundle found on this machine (install ca-certificates): clients would lose trust in the AI providers' certificates")


def build_bundle(d: pathlib.Path) -> pathlib.Path:
    """A COMBINED trust file: public CAs + the estate's CA. Never our CA alone - that would break every call to a cloud AI provider."""
    out = d / "ca-bundle.pem"
    out.write_text(system_ca_bundle().rstrip("\n") + "\n" + (d / "ca.crt").read_text("utf-8"), "utf-8")
    os.chmod(out, 0o644)
    return out


def issue_internal(d: pathlib.Path) -> list[str]:
    """One certificate + key per service (its own, so one compromised container cannot speak for another)."""
    exe = need_openssl()
    sub = d / "internal"
    sub.mkdir(exist_ok=True)
    os.chmod(sub, 0o755)
    made = []
    for svc, _port, _loop in INTERNAL:
        crt = sub / f"{svc}.crt"
        info = cert_info(crt)
        if info and (info.get("days_left") or 0) >= RENEW_WITHIN_DAYS and f"{svc}.securax.internal" in info.get("names", []):
            continue
        with tempfile.TemporaryDirectory() as t:
            ext = pathlib.Path(t) / "ext.cnf"
            ext.write_text("basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth\n"
                           f"subjectAltName=DNS:{svc}.securax.internal\n")
            csr = pathlib.Path(t) / "s.csr"
            key = sub / f"{svc}.key"
            r = run([exe, "req", "-new", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", str(key), "-out", str(csr), "-subj", f"/CN={svc}.securax.internal"])
            if r.returncode:
                raise SystemExit(f"openssl could not create the {svc} key:\n" + r.stderr)
            # the sidecar's nginx master runs as root and reads its key at start; keep it owner-only anyway
            os.chmod(key, 0o600)
            r = run([exe, "x509", "-req", "-in", str(csr), "-CA", str(d / "ca.crt"), "-CAkey", str(d / "ca.key"), "-CAcreateserial", "-days", str(DAYS_SERVER),
                     "-sha256", "-extfile", str(ext), "-out", str(crt)])
            if r.returncode:
                raise SystemExit(f"openssl could not sign the {svc} certificate:\n" + r.stderr)
        os.chmod(crt, 0o644)
        made.append(svc)
    (d / "ca.srl").unlink(missing_ok=True)
    return made


# ───────────────────────────────────────────── probing ─────────────────────────────────────────────
def probe(name: str, ca: pathlib.Path, host: str = "127.0.0.1", port: int = 443, timeout: float = 3) -> dict:
    """A real TLS handshake to the edge presenting `name` (SNI), verified against our CA, then one HTTP request to learn the status."""
    ctx = ssl.create_default_context(cafile=str(ca))
    try:
        with socket.create_connection((host, port), timeout=timeout) as s, ctx.wrap_socket(s, server_hostname=name) as t:
            version, cipher = t.version(), t.cipher()[0]            # read before the request: a server may close straight after the handshake
            t.sendall(f"GET / HTTP/1.1\r\nHost: {name}\r\nConnection: close\r\n\r\n".encode())
            try:
                first = t.recv(64).split(b"\r\n")[0].decode("latin-1", "replace")
            except (OSError, ssl.SSLError):
                first = ""
            m = re.match(r"HTTP/\S+ (\d{3})", first)
            return {"ok": True, "tls": version, "cipher": cipher, "http": int(m.group(1)) if m else None}
    except ssl.SSLError as e:
        return {"ok": False, "why": f"TLS refused: {e.reason or e}"}
    except OSError as e:
        return {"ok": False, "why": f"not answering ({type(e).__name__})"}


def plain_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=1) as s:
            s.sendall(b"GET / HTTP/1.0\r\n\r\n")
            return s.recv(5).startswith(b"HTTP")
    except OSError:
        return False


def resolves(fqdn: str) -> str | None:
    """Does this machine's resolver know the name? (*.localhost is resolved by the browser itself, so it counts as fine.)"""
    try:
        return socket.getaddrinfo(fqdn, None)[0][4][0]
    except OSError:
        return "browser" if fqdn.endswith(".localhost") else None


def status(as_json: bool = False) -> int:
    d = tls_dir()
    on = tls_is_on()
    dom = domain()
    info = cert_info(d / "server.crt")
    rows = []
    for label, name, _svc, _port, plain in ENDPOINTS:
        fq = host_of(name, dom)
        p = probe(fq, d / "ca.crt") if (d / "ca.crt").exists() else {"ok": False, "why": "no CA yet (./securax tls on)"}
        rows.append({"label": label, "name": fq, "https": p, "dns": resolves(fq), "plain_port": plain, "plain_open": plain_open(plain)})
    worst = 0
    if as_json:
        print(json.dumps({"enabled": on, "domain": dom, "dir": str(d), "cert": info, "endpoints": rows, "internal_tls": tls_internal_on(), "internal_hops_not_encrypted": [] if tls_internal_on() else INTERNAL_HOPS, "internal_exceptions": INTERNAL_EXCEPTIONS if tls_internal_on() else []}, indent=2))
    else:
        print(f"TLS edge: {'ON' if on else 'off'}   domain: {dom}   certificate store: {d}")
        if info:
            dl = info.get("days_left")
            print(f"  server certificate: {dl} days left" + ("  ⚠ renew: ./securax tls renew" if dl is not None and dl < RENEW_WITHIN_DAYS else ""))
            print("  covers: " + ", ".join(info.get("names", [])))
        else:
            print("  no certificate yet:  ./securax tls on")
        for r in rows:
            h = r["https"]
            line = f"  {r['label']:<30} https://{r['name']:<34} " + (f"✔ {h['tls']}" if h["ok"] else f"✘ {h['why']}")
            if r["dns"] is None:
                line += f"   ⚠ this machine cannot resolve {r['name']}: add a DNS record (*.{dom} -> this machine's address) or a hosts-file line"
            if r["plain_open"] and on and r["plain_port"] == 8080:
                line += "   · plain 127.0.0.1:8080 kept for the CLI (this machine only)"
            elif r["plain_open"]:
                line += f"   ⚠ plain http://localhost:{r['plain_port']} still answers"
            print(line)
        if tls_internal_on():
            print("  Internal TLS: ON (services listen on loopback; sidecars terminate TLS; clients trust your CA). Exception: " + "; ".join(INTERNAL_EXCEPTIONS))
        else:
            print("  Not yet encrypted (private Docker networks only, never leave this machine; turn on with ./securax tls internal on): " + "; ".join(INTERNAL_HOPS))
    if on:
        for r in rows:
            if not r["https"]["ok"]:
                worst = 1
            if r["plain_open"] and r["plain_port"] != 8080:
                worst = 1
    if info and (info.get("days_left") or 0) < 14:
        worst = 2
    return worst


# ───────────────────────────────────────────── trust ─────────────────────────────────────────────
def in_wsl() -> bool:
    try:
        return "microsoft" in pathlib.Path("/proc/version").read_text().lower()
    except OSError:
        return False


def cmd_trust(apply: bool) -> int:
    ca = tls_dir() / "ca.crt"
    if not ca.exists():
        print("no CA yet:  ./securax tls on")
        return 1
    print(f"The CA certificate is {ca}  (the public half only - safe to copy; never share ca.key).")
    print("It can only vouch for localhost, private/Tailscale addresses, *.securax.internal and your chosen domain, so trusting it cannot be used against real websites.\n")
    if in_wsl() and shutil.which("powershell.exe"):
        win = run(["wslpath", "-w", str(ca)]).stdout.strip()
        cmd = f"Import-Certificate -FilePath '{win}' -CertStoreLocation Cert:\\CurrentUser\\Root"
        print("Windows (Edge/Chrome use the Windows store). Run this in Ubuntu:")
        print(f"  powershell.exe -NoProfile -Command \"{cmd}\"")
        print("Windows shows a security prompt: read the name (SecuRAX Local CA) and choose Yes. Then CLOSE AND REOPEN the browser.")
        print("Firefox keeps its own store: Settings > Privacy & Security > View Certificates > Authorities > Import.")
        if apply:
            r = subprocess.run(["powershell.exe", "-NoProfile", "-Command", cmd])
            return r.returncode
    elif sys.platform == "darwin":
        print(f"macOS:  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain {ca}")
    else:
        print(f"Linux (system):  sudo cp {ca} /usr/local/share/ca-certificates/securax-ca.crt && sudo update-ca-certificates")
        print("Chrome/Edge/Firefox on Linux use their own store: Settings > Privacy > Manage certificates > Authorities > Import.")
    print("\nOther devices (phone/iPad): send them ca.crt over a channel you trust and install it as a trusted CA; iOS also needs Settings > General > About > Certificate Trust Settings.")
    return 0


# ───────────────────────────────────────────── commands ─────────────────────────────────────────────
PORT_CLASH = re.compile(r"ports are not available|port is already allocated|address already in use", re.I)


def http_port() -> str:
    """The host port of the plain-HTTP redirect: 80, or ALT_HTTP_PORT when another program holds 80."""
    return read_env().get("TLS_HTTP_PORT") or "80"


ALT_HTTP_PORT = "8880"


def edge_ports_taken() -> list[str]:
    """Ports 443 and the redirect port already held by another program (on Windows often IIS, a VPN or another web
    server). Checked with a throw-away container that only binds them, because from Ubuntu on WSL the Windows side's
    listeners are invisible. [] when free, when the edge itself holds them, or when Docker cannot be asked (the start-up
    fallback still covers it)."""
    if not shutil.which("docker"):
        return []
    try:
        mine = subprocess.run(["docker", "ps", "-q", "--filter", "label=com.docker.compose.service=tls-edge"],
                              capture_output=True, text=True, timeout=20).stdout.strip()
        if mine:
            return []
        bind = read_env().get("BIND_HOST") or "127.0.0.1"
        hp = http_port()
        r = subprocess.run(["docker", "run", "--rm", "-p", f"{bind}:443:443", "-p", f"{bind}:{hp}:80", "nginx:1.30-alpine", "true"],
                           capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if r.returncode and PORT_CLASH.search(r.stderr):
        return sorted(set(re.findall(rf":(443|{re.escape(hp)})\b", r.stderr))) or [f"{hp}/443"]
    return []


def windows_owner(port: str) -> str:
    """The name of the Windows program listening on PORT, asked through PowerShell from WSL. '' when it cannot be asked
    (not on WSL, or WSL cannot run Windows programs right now)."""
    if not shutil.which("powershell.exe"):
        return ""
    ps = (f"Get-NetTCPConnection -State Listen -LocalPort {int(port)} -ErrorAction SilentlyContinue | "
          "ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; \"$($_.OwningProcess) $($p.ProcessName)\" } | "
          "Sort-Object -Unique")
    try:
        r = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return ", ".join(ln.strip() for ln in r.stdout.splitlines() if ln.strip())


def explain_taken(port: str) -> None:
    owner = windows_owner(port)
    if owner:
        print(f"  It is held by (PID and name): {owner}.")
        if owner.split()[0] == "4":
            print("  PID 4 is Windows itself, serving for a service such as IIS (World Wide Web Publishing), SQL Server")
            print("  Reporting Services or BranchCache. In Windows PowerShell:  netsh http show servicestate  names it.")
    else:
        print("  To find the program, open Windows PowerShell from the Start menu (not this Ubuntu window) and run:")
        print(f"    netstat -ano | findstr :{port}     (the last number is its PID; Task Manager > Details shows its name)")


def cmd_on(extra: list[str], dom: str | None, new_ca: bool) -> int:
    if dom and not valid_domain(dom):
        print(f"'{dom}' is not a valid domain name (example: securax.example.in)")
        return 2
    dom = (dom or domain()).lower()
    res = ensure(extra, force=False, dom=dom, new_ca=new_ca)
    if res["refused"]:
        print("These names are outside what the CA is allowed to vouch for, so they are NOT in the certificate: " + ", ".join(res["refused"]))
        print("  (allowed: localhost, private/Tailscale IPs, *.ts.net, *.local, *.securax.internal, this machine's own name" + (f", {dom}" if dom != DEFAULT_DOMAIN else "") + ")")
    set_env("TLS_DIR", res["dir"])
    set_env("SECURAX_DOMAIN", dom)
    set_env("COMPOSE_FILE", TLS_COMPOSE)
    set_env("COMPOSE_PATH_SEPARATOR", ":")
    write_edge_conf(dom)
    print(f"✔ certificate ready ({res['cert'].get('days_left')} days left) for: {', '.join(res['names'])}")
    print(f"✔ HTTPS edge enabled; every service is reached by NAME on port 443 under {dom}")
    print("\n⚠ READ THIS FIRST - your browser keeps each address's data separately.")
    print(f"  The Guiding Map / Life OS stores its data in the browser PER ADDRESS. https://hub.{dom} is a NEW address, so it starts empty")
    print("  (your data is not lost: it stays under http://localhost:8088 and returns if you run './securax tls off').")
    print("  Before you switch: open the app on the OLD address > Ops > System health > Export backup. On the new address: import it,")
    print("  or turn cross-device sync on (it restores everything). Chat, documents and n8n live on the server and are unaffected; you sign in to Chat again.")
    print("\nNext:")
    print("  1. ./securax tls trust --apply      (once per computer/browser; Windows asks you to confirm)")
    print("  2. ./securax down && ./securax up")
    print(f"  3. open https://hub.{dom}/hub.html      (Chat: https://chat.{dom})")
    if dom != DEFAULT_DOMAIN:
        print(f"  4. DNS: one wildcard record  *.{dom}  ->  this machine's private/Tailscale address (that record is the only place the address lives)")
    print("  5. ./securax tls status")
    return 0


def cmd_internal(on: bool) -> int:
    if not tls_is_on():
        print("Turn the HTTPS edge on first:  ./securax tls on")
        return 2
    if not on:
        set_env("TLS_INTERNAL", None)
        set_env("COMPOSE_FILE", TLS_COMPOSE)
        write_edge_conf()
        print("Internal TLS off. Restart to apply:  ./securax down && ./securax up   (the services talk plain HTTP on the private Docker network again)")
        return 0
    d = tls_dir()
    made = issue_internal(d)
    bundle = build_bundle(d)
    set_env("TLS_INTERNAL", "1")
    set_env("COMPOSE_FILE", TLS_COMPOSE_INTERNAL)
    write_edge_conf()
    print(f"✔ certificates for {', '.join(n for n, _p, _l in INTERNAL)} ({'issued: ' + ', '.join(made) if made else 'already valid'})")
    print(f"✔ trust file with the public CAs + yours: {bundle}")
    print("✔ the services now listen on loopback only; each has a TLS sidecar; the CLI and agents talk to the gateway over HTTPS through the edge (https://localhost)")
    print("  Exception, stated plainly: " + "; ".join(INTERNAL_EXCEPTIONS))
    print("\nNext:  ./securax down && ./securax up   then  ./securax tls status")
    return 0


def cmd_off() -> int:
    set_env("COMPOSE_FILE", None)
    set_env("COMPOSE_PATH_SEPARATOR", None)
    set_env("TLS_INTERNAL", None)
    print("TLS edge off. Restart to apply:  ./securax down && ./securax up   (plain http://localhost:8088 etc. return; browsers will say 'not secure')")
    return 0


def cmd_renew() -> int:
    res = ensure(None, force=True)
    if tls_internal_on():
        for svc, _p, _l in INTERNAL:
            (tls_dir() / "internal" / f"{svc}.crt").unlink(missing_ok=True)
        issue_internal(tls_dir())
        build_bundle(tls_dir())
    write_edge_conf()
    print(f"✔ new server certificate, {res['cert'].get('days_left')} days left. Restart the edge:  (cd local/compose && docker compose --profile ai restart tls-edge)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    on = sub.add_parser("on")
    on.add_argument("--domain", default="", help="the domain the estate lives under (default securax.localhost: no DNS needed on this machine)")
    on.add_argument("--hosts", default="", help="extra names/addresses to cover, comma separated")
    on.add_argument("--new-ca", action="store_true", help="create a NEW authority (needed to add a domain the old one cannot vouch for; devices must trust it again)")
    sub.add_parser("off")
    sub.add_parser("renew")
    sub.add_parser("render")
    it = sub.add_parser("internal")
    it.add_argument("state", choices=["on", "off"])
    tr = sub.add_parser("trust")
    tr.add_argument("--apply", action="store_true")
    st = sub.add_parser("status")
    st.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "on":
        taken = edge_ports_taken()
        if taken == ["80"]:
            # Port 80 only redirects to https, so it need not be 80: move it, and HTTPS on 443 works exactly the same.
            set_env("TLS_HTTP_PORT", ALT_HTTP_PORT)
            print(f"  Port 80 is used by another program on this computer, so the http-to-https redirect moves to {ALT_HTTP_PORT}.")
            print("  Nothing else changes: type the https:// addresses (the Command Center links already do).")
            taken = edge_ports_taken()
        if taken:
            print(f"✗ Port {' and '.join(taken)} on this computer is already used by another program, so the HTTPS names cannot start.")
            print("  Nothing was changed: keep using http://localhost:8088 (it works the same).")
            explain_taken(taken[0].split("/")[0])
            print("  Stop that program, then run  ./securax tls on  again.")
            return 1
        return cmd_on([h for h in a.hosts.split(",") if h], a.domain or None, a.new_ca)
    if a.cmd == "off":
        return cmd_off()
    if a.cmd == "renew":
        return cmd_renew()
    if a.cmd == "render":
        print(write_edge_conf())
        return 0
    if a.cmd == "internal":
        return cmd_internal(a.state == "on")
    if a.cmd == "trust":
        return cmd_trust(a.apply)
    return status(a.json)


if __name__ == "__main__":
    sys.exit(main())
