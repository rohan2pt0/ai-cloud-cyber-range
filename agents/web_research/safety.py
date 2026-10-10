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
from urllib.parse import urlparse

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


# Verbs/paths that smell like a state-changing action — queued for a human, never auto-run.
_WRITE_HINTS = re.compile(
    r"\b(login|signin|sign-in|logout|checkout|buy|purchase|order|pay|payment|add[-_ ]?to[-_ ]?cart|"
    r"subscribe|register|signup|sign-up|submit|post|delete|remove|transfer|book|apply|upload|"
    r"confirm|wire|withdraw)\b", re.I)


def is_state_changing(method: str, url: str, intent: str = "") -> bool:
    """Heuristic: anything that is not a GET/HEAD, or whose URL/intent reads like a write, is
    treated as state-changing and must go through human-in-the-loop approval."""
    if method.upper() not in {"GET", "HEAD"}:
        return True
    probe = f"{urlparse(url).path} {urlparse(url).query} {intent}"
    return bool(_WRITE_HINTS.search(probe))


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
            if best is None or cand[0] > best[0]:
                best = cand
    return best[1] if best is not None else True
