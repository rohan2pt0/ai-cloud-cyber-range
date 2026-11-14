"""Web push from the estate (zero-setup, owner 2026-11-14): alerts reach the phone through the Life OS itself.

No second app, no topic, no token to copy. The estate makes its own VAPID key pair the first time it is needed and keeps
it next to its database (0600); a paired Life OS asks for the public half, the person taps Allow once, and the browser's
subscription comes back here over the existing device-token sync. Messages are sent from inside the container
(`python -m syncsvc.push send`), so there is no new network door and no new secret.

    python -m syncsvc.push send "text" [--title T] [--user U]   exit 0 sent to at least one device, 2 none subscribed, 1 failed
    python -m syncsvc.push count [--user U]                      how many devices would receive it

The standards: RFC 8291 (message encryption, aes128gcm), RFC 8292 (VAPID, ES256), RFC 8030 (TTL, Urgency).
Only https endpoints on the browsers' own push services are accepted, so the estate can never be made to post elsewhere.
What leaves: a title and a short line (counts and labels; governance/notify.py already keeps it to that), encrypted so
the push service cannot read it.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from contextlib import closing
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAX_PER_USER = int(os.environ.get("SYNC_PUSH_MAX_DEVICES", "10"))
MAX_PAYLOAD = 3000          # push services accept about 4 KB; keep well under it after encryption
# The browsers' own push services (Chrome/Android, Firefox, Safari/iOS, Edge). Anything else is refused: no SSRF.
PUSH_HOSTS = ("fcm.googleapis.com", "updates.push.services.mozilla.com", ".push.apple.com", ".notify.windows.com")


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def unb64u(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _db_path() -> str:
    return os.environ.get("SYNC_DB_PATH", "/data/estate-sync.db")


def key_path() -> str:
    return os.environ.get("SYNC_PUSH_KEY", os.path.join(os.path.dirname(_db_path()) or ".", "vapid.pem"))


def vapid_key() -> ec.EllipticCurvePrivateKey:
    """The estate's VAPID key: made once, kept on the estate only (0600), never printed or synced."""
    p = key_path()
    try:
        with open(p, "rb") as f:
            return serialization.load_pem_private_key(f.read(), password=None)
    except FileNotFoundError:
        pass
    k = ec.generate_private_key(ec.SECP256R1())
    pem = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    fd = os.open(p + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(pem)
    try:
        os.link(p + ".tmp", p)            # first writer wins if two start together; the other reads the winner's key
    except FileExistsError:
        pass
    os.unlink(p + ".tmp")
    with open(p, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def _raw_pub(k) -> bytes:
    return k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)


def public_key() -> str:
    """The applicationServerKey the Life OS passes to pushManager.subscribe (65 bytes, base64url)."""
    return b64u(_raw_pub(vapid_key()))


# ── Subscriptions ────────────────────────────────────────────────────────────────────────────────────────────────────
def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path(), timeout=10)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("CREATE TABLE IF NOT EXISTS push_subs (user_id TEXT NOT NULL, endpoint TEXT PRIMARY KEY, p256dh TEXT NOT NULL,"
                 " auth TEXT NOT NULL, label TEXT, created_at INTEGER NOT NULL)")
    return conn


def endpoint_problem(endpoint: str) -> str | None:
    """None when the endpoint is an https URL on a browser push service; else why it is refused."""
    if not isinstance(endpoint, str) or len(endpoint) > 1024:
        return "the endpoint is missing or too long"
    u = urlsplit(endpoint)
    host = (u.hostname or "").lower()
    if u.scheme != "https" or u.username or u.password or u.port not in (None, 443):
        return "the endpoint must be a plain https URL"
    if not any(host == h or (h.startswith(".") and host.endswith(h)) for h in PUSH_HOSTS):
        return "the endpoint is not a browser push service"
    return None


def subscribe(user: str, sub: dict, label: str = "") -> int:
    """Store one browser subscription for this user (the newest MAX_PER_USER are kept). Returns the user's device count."""
    if not isinstance(sub, dict):
        raise ValueError("send the browser's subscription as JSON")
    endpoint = sub.get("endpoint")
    why = endpoint_problem(endpoint)
    if why:
        raise ValueError(why)
    keys = sub.get("keys") if isinstance(sub.get("keys"), dict) else {}
    try:
        p256dh, auth = unb64u(str(keys.get("p256dh", ""))), unb64u(str(keys.get("auth", "")))
    except (ValueError, TypeError):
        raise ValueError("the subscription keys are not base64url")
    if len(p256dh) != 65 or p256dh[0] != 4 or len(auth) != 16:
        raise ValueError("the subscription keys have the wrong shape")
    ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), p256dh)     # a point on the curve, or ValueError
    with closing(_db()) as conn:
        conn.execute("INSERT INTO push_subs(user_id, endpoint, p256dh, auth, label, created_at) VALUES(?,?,?,?,?,?) "
                     "ON CONFLICT(endpoint) DO UPDATE SET user_id=excluded.user_id, p256dh=excluded.p256dh, auth=excluded.auth,"
                     " label=excluded.label, created_at=excluded.created_at",
                     (user, endpoint, b64u(p256dh), b64u(auth), str(label)[:40], int(time.time())))
        rows = conn.execute("SELECT endpoint FROM push_subs WHERE user_id=? ORDER BY created_at DESC, rowid DESC", (user,)).fetchall()
        for (old,) in rows[MAX_PER_USER:]:
            conn.execute("DELETE FROM push_subs WHERE endpoint=?", (old,))
        conn.commit()
        return min(len(rows), MAX_PER_USER)


def unsubscribe(user: str, endpoint: str) -> bool:
    with closing(_db()) as conn:
        n = conn.execute("DELETE FROM push_subs WHERE user_id=? AND endpoint=?", (user, endpoint)).rowcount
        conn.commit()
        return n > 0


def subscriptions(user: str | None = None) -> list[dict]:
    with closing(_db()) as conn:
        q = "SELECT user_id, endpoint, p256dh, auth FROM push_subs" + (" WHERE user_id=?" if user else "")
        return [{"user": u, "endpoint": e, "p256dh": p, "auth": a} for u, e, p, a in conn.execute(q, (user,) if user else ())]


# ── RFC 8291 and RFC 8292 ────────────────────────────────────────────────────────────────────────────────────────────
def _hkdf(salt: bytes, ikm: bytes, info: bytes, n: int) -> bytes:
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    return hmac.new(prk, info + b"\x01", hashlib.sha256).digest()[:n]


def encrypt(payload: bytes, p256dh: bytes, auth: bytes, salt: bytes | None = None,
            server_key: ec.EllipticCurvePrivateKey | None = None) -> bytes:
    """One aes128gcm record (RFC 8291 section 3 and RFC 8188): salt, record size, the sender's key, the ciphertext."""
    salt = salt or os.urandom(16)
    as_key = server_key or ec.generate_private_key(ec.SECP256R1())      # a fresh key per message
    as_pub = _raw_pub(as_key)
    ua_pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), p256dh)
    shared = as_key.exchange(ec.ECDH(), ua_pub)
    ikm = _hkdf(auth, shared, b"WebPush: info\x00" + p256dh + as_pub, 32)
    cek = _hkdf(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = _hkdf(salt, ikm, b"Content-Encoding: nonce\x00", 12)
    ct = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)            # 0x02: the last (only) record
    return salt + (4096).to_bytes(4, "big") + bytes([len(as_pub)]) + as_pub + ct


def vapid_header(endpoint: str, key: ec.EllipticCurvePrivateKey | None = None, now: float | None = None) -> str:
    """Authorization: vapid t=<ES256 JWT for the push service's origin>, k=<our public key> (RFC 8292)."""
    key = key or vapid_key()
    u = urlsplit(endpoint)
    claims = {"aud": f"{u.scheme}://{u.hostname}", "exp": int((now or time.time()) + 12 * 3600),
              "sub": os.environ.get("SYNC_PUSH_SUBJECT", "https://localhost")}
    head = b64u(json.dumps({"typ": "JWT", "alg": "ES256"}, separators=(",", ":")).encode())
    body = b64u(json.dumps(claims, separators=(",", ":")).encode())
    r, s = decode_dss_signature(key.sign(f"{head}.{body}".encode(), ec.ECDSA(hashes.SHA256())))
    sig = b64u(r.to_bytes(32, "big") + s.to_bytes(32, "big"))
    return f"vapid t={head}.{body}.{sig}, k={b64u(_raw_pub(key))}"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect could lead off the push services' hosts (SSRF): it is never followed, and counts as a failure."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _post(endpoint: str, body: bytes, headers: dict, timeout: int = 10) -> int:
    req = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with _OPENER.open(req, timeout=timeout) as r:      # https on a push service only
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def send(text: str, title: str = "SecuRAX", user: str | None = None, poster=_post) -> dict:
    """Send one message to every subscribed device (of one user, or all). A device the push service no longer knows
    (404 or 410) is removed: the person turned it off or uninstalled the app."""
    payload = json.dumps({"title": str(title)[:80], "body": str(text)[:MAX_PAYLOAD]}, ensure_ascii=False).encode()[:MAX_PAYLOAD]
    out = {"sent": 0, "gone": 0, "failed": 0}
    for s in subscriptions(user):
        if endpoint_problem(s["endpoint"]):
            out["failed"] += 1
            continue
        body = encrypt(payload, unb64u(s["p256dh"]), unb64u(s["auth"]))
        code = poster(s["endpoint"], body, {"Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream",
                                            "TTL": "86400", "Urgency": "normal", "Authorization": vapid_header(s["endpoint"])})
        if 200 <= code < 300:
            out["sent"] += 1
        elif code in (404, 410):
            unsubscribe(s["user"], s["endpoint"])
            out["gone"] += 1
        else:
            out["failed"] += 1
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m syncsvc.push", description=__doc__.split("\n\n")[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    s1 = sp.add_parser("send")
    s1.add_argument("text", nargs="?", help="the message; read from standard input when left out")
    s1.add_argument("--title", default="SecuRAX")
    s1.add_argument("--user")
    s2 = sp.add_parser("count")
    s2.add_argument("--user")
    a = ap.parse_args(argv)
    if a.cmd == "count":
        print(len(subscriptions(a.user)))
        return 0
    text = a.text if a.text is not None else sys.stdin.read()
    if not subscriptions(a.user):
        print("no device has allowed alerts yet: open the Life OS and tap Allow alerts", file=sys.stderr)
        return 2
    r = send(text.strip(), a.title, a.user)
    print(json.dumps(r))
    return 0 if r["sent"] else 1


if __name__ == "__main__":
    sys.exit(main())
