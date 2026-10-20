"""Sign-in by Cloudflare Access (doc 85): a device that came through your Access gate needs no sync token.

Cloudflare Access puts a signed token in every request it lets through (header Cf-Access-Jwt-Assertion). This module checks that
token here, at the origin, instead of trusting that a request came through Cloudflare: the signature against your team's published
keys, the issuer (your team), the audience (your SecuRAX application) and the expiry, then the e-mail against SYNC_ACCESS_EMAILS.
A request without a valid token is treated exactly as before (it needs a device token), so this only ever adds a way in for you.

    SYNC_ACCESS_TEAM    your team's sign-in domain, e.g. myteam.cloudflareaccess.com (written by ./securax online setup)
    SYNC_ACCESS_AUD     the application's AUD tag (same)
    SYNC_ACCESS_EMAILS  who may sync (comma-separated); everyone else is refused even if Access let them in
    SYNC_ACCESS_USER    whose data they see (default "me", the name every device already uses)

Standard library only. The RS256 check is the gateway's (apps/llm-gateway/app/identity.py): it rebuilds the exact padded message
and compares, so there is no padding parsing to get wrong.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import threading
import time
import urllib.request

LEEWAY_S = 60
_SHA256_DIGESTINFO = bytes.fromhex("3031300d060960864801650304020105000420")
_lock = threading.Lock()
_keys: dict[str, dict] = {}
_fetched = 0.0


class Denied(Exception):
    pass


def configured() -> bool:
    return bool(os.environ.get("SYNC_ACCESS_TEAM") and os.environ.get("SYNC_ACCESS_AUD") and _emails())


def _emails() -> set[str]:
    return {e.strip().lower() for e in os.environ.get("SYNC_ACCESS_EMAILS", "").split(",") if e.strip()}


def user() -> str:
    return os.environ.get("SYNC_ACCESS_USER", "me").strip() or "me"


def _team() -> str:
    t = os.environ.get("SYNC_ACCESS_TEAM", "").strip().lower()
    return t.removeprefix("https://").rstrip("/")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _rsa_verify(n: int, e: int, msg: bytes, sig: bytes) -> bool:
    k = (n.bit_length() + 7) // 8
    if n.bit_length() < 2048 or e < 3 or e % 2 == 0 or len(sig) != k:
        return False
    s = int.from_bytes(sig, "big")
    if s >= n:
        return False
    em = pow(s, e, n).to_bytes(k, "big")
    t = _SHA256_DIGESTINFO + hashlib.sha256(msg).digest()
    return hmac.compare_digest(em, b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t)


def _fetch_keys() -> dict[str, dict]:
    """Your team's signing keys. Cloudflare rotates them, so an unknown key id triggers a refetch, at most once a minute."""
    with urllib.request.urlopen(f"https://{_team()}/cdn-cgi/access/certs", timeout=5) as r:      # noqa: S310 (fixed https URL)
        doc = json.loads(r.read())
    return {k.get("kid", ""): k for k in doc.get("keys", []) if k.get("kty") == "RSA"}


def _key(kid: str, fetch=_fetch_keys) -> dict | None:
    global _keys, _fetched
    with _lock:
        if kid not in _keys and time.time() - _fetched > 60:
            _fetched = time.time()
            try:
                _keys = fetch()
            except (OSError, ValueError):
                pass                                   # keep the old keys; a token signed by an unknown key is refused below
        return _keys.get(kid)


def verify(token: str, now: float | None = None, fetch=_fetch_keys) -> str:
    """The signed-in e-mail, or Denied with the reason."""
    now = time.time() if now is None else now
    try:
        h_b, p_b, s_b = token.split(".")
        header, claims, sig = json.loads(_b64d(h_b)), json.loads(_b64d(p_b)), _b64d(s_b)
    except (ValueError, TypeError) as exc:
        raise Denied("not a well-formed token") from exc
    if not isinstance(header, dict) or not isinstance(claims, dict) or header.get("alg") != "RS256":
        raise Denied("only RS256 tokens from Cloudflare Access are accepted")
    jwk = _key(str(header.get("kid", "")), fetch)
    if not jwk:
        raise Denied("signed by a key your Access team does not publish")
    if not _rsa_verify(int.from_bytes(_b64d(jwk["n"]), "big"), int.from_bytes(_b64d(jwk["e"]), "big"), f"{h_b}.{p_b}".encode(), sig):
        raise Denied("bad signature")
    if not isinstance(claims.get("exp"), (int, float)) or now > claims["exp"] + LEEWAY_S:
        raise Denied("expired")
    if isinstance(claims.get("nbf"), (int, float)) and now + LEEWAY_S < claims["nbf"]:
        raise Denied("not valid yet")
    if claims.get("iss") != f"https://{_team()}":
        raise Denied("issued by another Access team")
    aud = claims.get("aud")
    if os.environ.get("SYNC_ACCESS_AUD") not in (aud if isinstance(aud, list) else [aud]):
        raise Denied("issued for another application")
    email = str(claims.get("email") or "").lower()
    if not email or email not in _emails():
        raise Denied("this account is not on the sync list (./securax online allow EMAIL)")
    return email
