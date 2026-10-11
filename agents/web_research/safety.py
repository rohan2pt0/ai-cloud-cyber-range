"""Safety rails for the autonomous web-research agent.

An agent that surfs the web on its own is useful and dangerous in equal measure. These
are the guardrails that make "autonomous" acceptable in a sovereign estate run by a
security professional:

  * SSRF guard   — it must never be steered into the estate's own services or a cloud
                   metadata endpoint (169.254.169.254). Autonomous fetchers are a classic
                   SSRF pivot; we block loopback, private, link-local and metadata targets.
  * Allowlist    — read-only browsing is confined to domains you approve (or everything
                   except an explicit denylist, if you opt into open browsing).
  * robots.txt   — we respect it; a polite crawler is a defensible one.
  * HITL on write — anything that changes state (login, form POST, purchase, posting) is
                   NEVER executed autonomously; it is queued for your approval.

Nothing here needs the network, so it is fully unit-tested offline.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

# Cloud metadata + obviously-internal hostnames an autonomous agent must never reach.
_BLOCKED_HOSTS = {
    "localhost", "metadata.google.internal", "metadata", "instance-data",
}
_METADATA_IPS = {"169.254.169.254", "100.100.100.200", "fd00:ec2::254"}

# Methods / schemes that change state or are non-web. Read-only research is GET/HEAD http(s).
_SAFE_SCHEMES = {"http", "https"}


def _host_ip(host: str):
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def is_safe_target(url: str) -> tuple[bool, str]:
    """True only for an http(s) URL that does not point at a private/loopback/link-local/
    metadata address. This is the SSRF gate — the first thing every fetch passes through."""
    try:
        p = urlparse(url)
    except ValueError:
        return False, "unparseable URL"
    if p.scheme not in _SAFE_SCHEMES:
        return False, f"scheme '{p.scheme}' is not http(s)"
    host = (p.hostname or "").lower()
    if not host:
        return False, "no host"
    if host in _BLOCKED_HOSTS:
        return False, f"host '{host}' is internal"
    if host in _METADATA_IPS:
        return False, "cloud metadata endpoint"
    ip = _host_ip(host)
    if ip is not None:
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified or str(ip) in _METADATA_IPS):
            return False, f"IP {ip} is private/loopback/link-local/reserved"
    # bare internal name with no dot (e.g. "gateway", "ollama") — refuse; research needs FQDNs
    if "." not in host and ip is None:
        return False, f"host '{host}' is not a public FQDN"
    return True, "ok"


def _ip_is_blocked(ip: "ipaddress._BaseAddress") -> bool:
    return (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
            or ip.is_multicast or ip.is_unspecified or str(ip) in _METADATA_IPS)


def resolved_ips_safe(host: str, resolver=socket.getaddrinfo) -> tuple[bool, str]:
    """DNS-level SSRF gate: resolve `host` and reject if ANY A/AAAA record is a private/loopback/
    link-local/metadata address. This closes the hole where a *public* hostname (which passes the
    syntactic `is_safe_target`) resolves to an internal IP (DNS rebinding / attacker-controlled
    DNS). `resolver` is injected so it is unit-tested offline. Call it at connect time, per hop."""
    if not host:
        return False, "no host"
    ip = _host_ip(host)
    if ip is not None:
        return (False, f"IP {ip} is internal") if _ip_is_blocked(ip) else (True, "ok")
    try:
        infos = resolver(host, None)
    except Exception as exc:  # noqa: BLE001 — resolution failure is fail-closed
        return False, f"DNS resolution failed ({str(exc)[:60]})"
    addrs = []
    for info in infos:
        sockaddr = info[4] if len(info) >= 5 else None
        if sockaddr:
            addrs.append(sockaddr[0])
    if not addrs:
        return False, "host did not resolve to any address"
    for a in addrs:
        try:
            if _ip_is_blocked(ipaddress.ip_address(a.split("%")[0])):
                return False, f"'{host}' resolves to internal address {a}"
        except ValueError:
            return False, f"'{host}' resolved to an unparseable address {a}"
    return True, "ok"


def follow_guarded(start_url: str, request_one, resolver=socket.getaddrinfo, max_redirects: int = 5):
    """Follow redirects manually, enforcing BOTH SSRF gates (syntactic + DNS) on every hop BEFORE
    the request is issued — so an internal/metadata request is never actually sent, even via a
    302 from an allowlisted page. `request_one(url) -> (status, location_or_None, body, final_url)`
    is injected (httpx in production, a fake in tests). Returns (status, body, final_url).
    Raises ValueError when a hop is blocked or the redirect limit is exceeded."""
    cur = start_url
    for _ in range(max_redirects + 1):
        ok, why = is_safe_target(cur)
        if not ok:
            raise ValueError(f"blocked target ({why})")
        ok, why = resolved_ips_safe(urlparse(cur).hostname or "", resolver)
        if not ok:
            raise ValueError(f"blocked by DNS gate ({why})")
        status, location, body, final_url = request_one(cur)
        if location:
            cur = urljoin(cur, location)      # resolve relative redirects, then re-guard next loop
            continue
        return status, body, final_url
    raise ValueError("too many redirects")


def _registrable(host: str) -> str:
    host = (host or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def domain_allowed(url: str, allow: list[str] | None, deny: list[str] | None) -> tuple[bool, str]:
    """Allowlist/denylist on the host. `allow=None or []` with `open_ok` is handled by the
    caller; here an empty allow means 'nothing is allowed' (fail-closed) unless a deny-only
    policy is chosen by passing allow=["*"]."""
    host = _registrable(urlparse(url).hostname or "")
    deny = [d.lower().lstrip(".") for d in (deny or [])]
    for d in deny:
        if host == d or host.endswith("." + d):
            return False, f"'{host}' is on the denylist"
    allow = [a.lower().lstrip(".") for a in (allow or [])]
    if allow == ["*"]:
        return True, "open browsing (deny-list only)"
    if not allow:
        return False, "no allowlist configured (fail-closed)"
    for a in allow:
        if host == a or host.endswith("." + a):
            return True, "on allowlist"
    return False, f"'{host}' is not on the allowlist"


# High-signal auth/payment/account PATH SEGMENTS. These are matched as whole URL path segments
# (bounded by '/'), NOT as substrings — so an article slug like '/post/how-to-apply-for-cover'
# is read normally, while a real '/login' or '/checkout' endpoint is deferred to a human. Low-signal
# words (post/apply/order/book/register/submit/…) are deliberately NOT here: on a GET they wreck
# research recall and a GET is not supposed to change state anyway.
_ACTION_SEGMENTS = {
    "login", "signin", "sign-in", "logout", "signout", "sign-out", "checkout", "cart", "basket",
    "payment", "pay", "billing", "account", "admin", "wp-admin", "wp-login", "wp-login.php",
    "oauth", "sso", "signup", "sign-up", "register", "password", "my-account",
}
# Query-string action markers (e.g. ?action=delete, ?do=login).
_ACTION_QUERY = re.compile(r"(?:^|&)(action|do|cmd|op)=", re.I)


def is_state_changing(method: str, url: str, intent: str = "") -> bool:
    """A step is state-changing (→ human-in-the-loop, never auto-run) if it is not a GET/HEAD, OR
    its URL is a real auth/payment/account endpoint. We match whole path segments so informational
    pages whose slug merely *contains* a verb (apply/order/post/…) are still read."""
    if method.upper() not in {"GET", "HEAD"}:
        return True
    p = urlparse(url)
    segments = {seg.lower() for seg in p.path.split("/") if seg}
    if segments & _ACTION_SEGMENTS:
        return True
    if _ACTION_QUERY.search(p.query or ""):
        return True
    return False


def robots_allows(robots_txt: str, path: str, agent: str = "*") -> bool:
    """Minimal, conservative robots.txt check for our user-agent / '*'. Unknown -> allowed,
    but an explicit Disallow that prefixes the path -> blocked. (Fetch the body with your own
    fetcher and pass it here; this stays offline-testable.)"""
    if not robots_txt:
        return True
    ua = None
    rules: dict[str, list[tuple[str, str]]] = {}
    for raw in robots_txt.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, val = (s.strip() for s in line.split(":", 1))
        k = key.lower()
        if k == "user-agent":
            ua = val.lower()
            rules.setdefault(ua, [])
        elif k in ("disallow", "allow") and ua is not None:
            rules.setdefault(ua, []).append((k, val))
    applicable = rules.get(agent.lower()) or rules.get("*") or []
    # Longest-match wins between Allow and Disallow (per the spec's common interpretation).
    best: tuple[int, bool] | None = None
    for k, val in applicable:
        if val == "":
            continue
        if path.startswith(val):
            cand = (len(val), k == "allow")
            # Longest match wins; on an equal-length tie, Allow beats Disallow (per the spec's
            # common interpretation), so a specific Allow can carve an exception out of a Disallow.
            if best is None or cand[0] > best[0] or (cand[0] == best[0] and cand[1] and not best[1]):
                best = cand
    return best[1] if best is not None else True
