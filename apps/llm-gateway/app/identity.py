"""Identity for the gateway: who is calling, in which role, how strongly they authenticated — and a refusal when that is not good enough.

Why this exists: regulators (RBI, SEBI, IRDAI, CERT-In, DPDP, ...) all converge on the same access-control asks — unique identity per
user, least-privilege roles, MFA for privileged access, lock-out after repeated failures, and an audit trail that names WHO did WHAT.
The gateway used to derive its "principal" from whatever Authorization string (or IP) arrived. This module replaces that with real
authentication, WITHOUT assuming which regulator, which identity provider, or which sector:

  AUTH_MODE            off (default: unchanged behaviour for a laptop) | optional (identify if a credential is sent, never refuse) | required
  Credentials          a signed JWT from ANY OIDC provider (Keycloak, Entra ID, Okta, Auth0, ...) and/or hashed service API keys
  OIDC_ISSUER / OIDC_AUDIENCE / OIDC_JWKS_URL | OIDC_JWKS_FILE | OIDC_JWKS_JSON   how to verify tokens (RS256; HS256 only with OIDC_HS256_SECRET)
  AUTH_ROLES_CLAIM     dotted path to the roles in the token (default `roles`; Keycloak realm roles: `realm_access.roles`)
  AUTH_ROLE_MAP        {"idp-role": "securax-role"} - securax roles are user, analyst, auditor, admin, service
  AUTH_MFA_ROLES       roles that must have authenticated with MFA (default admin,auditor); proven by the token's `amr`/`acr`
  AUTH_MAX_FAILURES / AUTH_FAILURE_WINDOW_S / AUTH_LOCKOUT_S     lock-out after repeated failures (default 5 / 300 s / 900 s)
  GATEWAY_API_KEYS     (or GATEWAY_API_KEYS_B64, the same base64-encoded) JSON list of {"id","sha256","roles","expires"?,"data_class"?}; only HASHES are stored (see governance/gateway_auth.py)

Standard library only: JWT signatures are verified here (RSASSA-PKCS1-v1_5/SHA-256 by exact comparison with the re-encoded message,
HMAC-SHA256) so the gateway's runtime dependency count and footprint do not grow. `alg: none` and algorithm confusion are refused:
the algorithm must be one the operator allowed, and an HS256 token is only ever checked against the HS256 secret, never a public key.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

ROLES = ("user", "analyst", "auditor", "admin", "service")
# endpoint -> roles allowed. admin may do everything; auditors are read-only; service accounts are machine callers.
ENDPOINT_ROLES: dict[str, frozenset[str]] = {
    "chat": frozenset({"user", "analyst", "admin", "service"}),
    "models": frozenset({"user", "analyst", "admin", "service", "auditor"}),
    "inspect": frozenset({"analyst", "admin", "service"}),
    "metrics": frozenset({"auditor", "admin", "service"}),
}
PUBLIC = {"healthz", "readyz", "version"}                    # liveness/readiness/version carry no data
_SHA256_DIGESTINFO = bytes.fromhex("3031300d060960864801650304020105000420")
DEFAULT_MFA_AMR = frozenset({"mfa", "otp", "totp", "hwk", "webauthn", "fido"})


class AuthError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


@dataclass
class Identity:
    subject: str = "anonymous"
    roles: tuple[str, ...] = ()
    method: str = "none"           # none | jwt | api_key
    mfa: bool = False
    data_class: str = ""           # optional default data classification for this caller (see residency.py)
    issuer: str = ""
    extra: dict = field(default_factory=dict)

    def audit(self) -> dict:
        return {"subject": self.subject, "roles": list(self.roles), "auth": self.method, "mfa": self.mfa}


# ----------------------------------------------------------------------------------------------------------------------- JWT
def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _rsa_verify(n: int, e: int, msg: bytes, sig: bytes) -> bool:
    """RSASSA-PKCS1-v1_5 / SHA-256, verified by rebuilding the exact encoded message and comparing (no padding parsing => no
    Bleichenbacher-style leniency)."""
    k = (n.bit_length() + 7) // 8
    if n.bit_length() < 2048 or e < 3 or e % 2 == 0 or len(sig) != k:
        return False
    s = int.from_bytes(sig, "big")
    if s >= n:
        return False
    em = pow(s, e, n).to_bytes(k, "big")
    t = _SHA256_DIGESTINFO + hashlib.sha256(msg).digest()
    expected = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
    return hmac.compare_digest(em, expected)


def _dig(obj: dict, path: str):
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


@dataclass
class Config:
    mode: str = "off"
    issuer: str = ""
    audience: str = ""
    jwks: dict = field(default_factory=dict)             # kid -> JWK
    jwks_url: str = ""
    algs: frozenset[str] = frozenset({"RS256"})
    hs256_secret: str = ""
    roles_claim: str = "roles"
    role_map: dict = field(default_factory=dict)
    mfa_roles: frozenset[str] = frozenset({"admin", "auditor"})
    mfa_amr: frozenset[str] = DEFAULT_MFA_AMR
    mfa_acr: frozenset[str] = frozenset()
    leeway_s: int = 60
    max_failures: int = 5
    failure_window_s: int = 300
    lockout_s: int = 900
    api_keys: list = field(default_factory=list)
    data_class_claim: str = "data_class"

    @classmethod
    def from_env(cls, env=None) -> Config:
        env = os.environ if env is None else env
        mode = env.get("AUTH_MODE", "off").strip().lower()
        if mode not in ("off", "optional", "required"):
            raise ValueError(f"AUTH_MODE must be off|optional|required, not {mode!r}")
        algs = {a.strip() for a in env.get("OIDC_ALGS", "RS256").split(",") if a.strip()}
        if "none" in {a.lower() for a in algs}:
            raise ValueError("the 'none' algorithm is never allowed")
        c = cls(mode=mode, issuer=env.get("OIDC_ISSUER", ""), audience=env.get("OIDC_AUDIENCE", ""), algs=frozenset(algs),
                hs256_secret=env.get("OIDC_HS256_SECRET", ""), roles_claim=env.get("AUTH_ROLES_CLAIM", "roles"),
                jwks_url=env.get("OIDC_JWKS_URL", ""), data_class_claim=env.get("AUTH_DATA_CLASS_CLAIM", "data_class"),
                leeway_s=int(env.get("AUTH_LEEWAY_S", "60")), max_failures=int(env.get("AUTH_MAX_FAILURES", "5")),
                failure_window_s=int(env.get("AUTH_FAILURE_WINDOW_S", "300")), lockout_s=int(env.get("AUTH_LOCKOUT_S", "900")))
        if env.get("AUTH_ROLE_MAP"):
            c.role_map = json.loads(env["AUTH_ROLE_MAP"])
        if env.get("AUTH_MFA_ROLES") is not None:
            c.mfa_roles = frozenset(r.strip() for r in env["AUTH_MFA_ROLES"].split(",") if r.strip())
        if env.get("AUTH_MFA_AMR"):
            c.mfa_amr = frozenset(a.strip() for a in env["AUTH_MFA_AMR"].split(",") if a.strip())
        if env.get("AUTH_MFA_ACR"):
            c.mfa_acr = frozenset(a.strip() for a in env["AUTH_MFA_ACR"].split(",") if a.strip())
        raw = env.get("OIDC_JWKS_JSON", "")
        if not raw and env.get("OIDC_JWKS_FILE"):
            with open(env["OIDC_JWKS_FILE"], encoding="utf-8") as f:
                raw = f.read()
        if raw:
            c.set_jwks(json.loads(raw))
        if env.get("GATEWAY_API_KEYS"):
            c.api_keys = json.loads(env["GATEWAY_API_KEYS"])
        elif env.get("GATEWAY_API_KEYS_B64"):            # same list, base64 - survives .env/compose quoting unchanged
            c.api_keys = json.loads(base64.b64decode(env["GATEWAY_API_KEYS_B64"]))
        if mode == "required" and not (c.jwks or c.jwks_url or c.hs256_secret or c.api_keys):
            raise ValueError("AUTH_MODE=required needs at least one way to authenticate: OIDC_JWKS_*, OIDC_HS256_SECRET or GATEWAY_API_KEYS")
        if "HS256" in c.algs and not c.hs256_secret:
            c.algs = frozenset(c.algs - {"HS256"})
        return c

    def set_jwks(self, doc: dict) -> None:
        self.jwks = {k.get("kid", ""): k for k in doc.get("keys", []) if k.get("kty") == "RSA"}


def verify_jwt(token: str, cfg: Config, now: float | None = None) -> Identity:
    now = time.time() if now is None else now
    try:
        h_b, p_b, s_b = token.split(".")
        header, claims, sig = json.loads(_b64d(h_b)), json.loads(_b64d(p_b)), _b64d(s_b)
    except (ValueError, TypeError) as exc:
        raise AuthError(401, "malformed_token", "token is not a well-formed JWT") from exc
    if not isinstance(header, dict) or not isinstance(claims, dict):
        raise AuthError(401, "malformed_token", "token is not a well-formed JWT")
    alg = header.get("alg")
    if not isinstance(alg, str) or alg.lower() == "none" or alg not in cfg.algs:
        raise AuthError(401, "bad_algorithm", f"token algorithm {alg!r} is not allowed")
    signing = f"{h_b}.{p_b}".encode()
    if alg == "HS256":
        good = hmac.compare_digest(hmac.new(cfg.hs256_secret.encode(), signing, hashlib.sha256).digest(), sig)
    elif alg == "RS256":
        jwk = cfg.jwks.get(header.get("kid", "")) or (next(iter(cfg.jwks.values())) if len(cfg.jwks) == 1 and not header.get("kid") else None)
        if not jwk:
            raise AuthError(401, "unknown_key", "token signed by an unknown key")
        good = _rsa_verify(int.from_bytes(_b64d(jwk["n"]), "big"), int.from_bytes(_b64d(jwk["e"]), "big"), signing, sig)
    else:
        raise AuthError(401, "bad_algorithm", f"token algorithm {alg!r} is not supported")
    if not good:
        raise AuthError(401, "bad_signature", "token signature is invalid")
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)):
        raise AuthError(401, "no_expiry", "token has no expiry")
    if now > exp + cfg.leeway_s:
        raise AuthError(401, "expired", "token has expired")
    if isinstance(claims.get("nbf"), (int, float)) and now + cfg.leeway_s < claims["nbf"]:
        raise AuthError(401, "not_yet_valid", "token is not valid yet")
    if cfg.issuer and claims.get("iss") != cfg.issuer:
        raise AuthError(401, "bad_issuer", "token issuer is not trusted")
    if cfg.audience:
        aud = claims.get("aud")
        if cfg.audience not in (aud if isinstance(aud, list) else [aud]):
            raise AuthError(401, "bad_audience", "token was not issued for this gateway")
    sub = claims.get("sub") or claims.get("preferred_username") or claims.get("email")
    if not sub:
        raise AuthError(401, "no_subject", "token has no subject")
    raw_roles = _dig(claims, cfg.roles_claim)
    raw_roles = raw_roles if isinstance(raw_roles, list) else ([raw_roles] if isinstance(raw_roles, str) else [])
    roles = tuple(sorted({cfg.role_map.get(r, r) for r in raw_roles if isinstance(r, str)} & set(ROLES)))
    amr = claims.get("amr") if isinstance(claims.get("amr"), list) else []
    mfa = bool(set(amr) & cfg.mfa_amr) or (bool(cfg.mfa_acr) and claims.get("acr") in cfg.mfa_acr)
    dc = claims.get(cfg.data_class_claim)
    return Identity(subject=str(sub), roles=roles, method="jwt", mfa=mfa, data_class=dc if isinstance(dc, str) else "",
                    issuer=str(claims.get("iss", "")))


# --------------------------------------------------------------------------------------------------------------- API keys
def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, cfg: Config, now: float | None = None) -> Identity | None:
    """Constant-time against every stored hash (no early exit), so timing does not reveal which key prefix matched."""
    now = time.time() if now is None else now
    digest, hit = hash_key(key), None
    for k in cfg.api_keys:
        if hmac.compare_digest(digest, str(k.get("sha256", ""))):
            hit = k
    if not hit:
        return None
    exp = hit.get("expires")
    if exp:
        try:
            if now > time.mktime(time.strptime(exp, "%Y-%m-%d")) + 86400:
                raise AuthError(401, "key_expired", "API key has expired")
        except ValueError:
            raise AuthError(401, "key_expired", "API key has an unreadable expiry; treated as expired") from None
    roles = tuple(sorted(set(hit.get("roles", [])) & set(ROLES)))
    return Identity(subject=f"key:{hit.get('id', 'unnamed')}", roles=roles, method="api_key", mfa=False, data_class=hit.get("data_class", ""))


# ------------------------------------------------------------------------------------------------------------- orchestration
class Authenticator:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._fails: dict[str, deque[float]] = defaultdict(deque)
        self._locked: dict[str, float] = {}
        self._jwks_at = 0.0

    # lock-out ----------------------------------------------------------------------------------------------------
    def locked(self, who: str, now: float) -> bool:
        until = self._locked.get(who, 0)
        if until > now:
            return True
        self._locked.pop(who, None)
        return False

    def record_failure(self, who: str, now: float) -> None:
        q = self._fails[who]
        q.append(now)
        while q and now - q[0] > self.cfg.failure_window_s:
            q.popleft()
        if len(q) >= self.cfg.max_failures:
            self._locked[who] = now + self.cfg.lockout_s
            q.clear()

    # credentials -------------------------------------------------------------------------------------------------
    @staticmethod
    def credential(headers) -> str:
        auth = headers.get("authorization") or ""
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        return (headers.get("x-api-key") or "").strip()

    async def refresh_jwks(self, fetch) -> None:
        """Re-read the provider's keys (at most once a minute) - rotation without a restart."""
        if not self.cfg.jwks_url or time.time() - self._jwks_at < 60:
            return
        self._jwks_at = time.time()
        try:
            self.cfg.set_jwks(await fetch(self.cfg.jwks_url))
        except Exception:  # noqa: BLE001 - keep serving with the keys we have; the failure shows up as 'unknown_key'
            pass

    async def authenticate(self, headers, client_ip: str, fetch=None, now: float | None = None) -> Identity:
        """Return the caller's Identity. In `off` mode everyone is anonymous. In `optional`, a bad credential is still refused
        (a wrong key is never silently downgraded to anonymous) but a missing one is allowed. In `required`, missing = 401."""
        now = time.time() if now is None else now
        if self.cfg.mode == "off":
            return Identity()
        cred = self.credential(headers)
        if not cred:
            if self.cfg.mode == "optional":
                return Identity()
            raise AuthError(401, "no_credentials", "authentication required")
        if self.locked(client_ip, now):
            raise AuthError(429, "locked_out", "too many failed attempts; try again later")
        try:
            ident = None
            if cred.count(".") == 2 and (self.cfg.jwks or self.cfg.jwks_url or self.cfg.hs256_secret):
                if fetch and self.cfg.jwks_url and not self.cfg.jwks:
                    await self.refresh_jwks(fetch)
                try:
                    ident = verify_jwt(cred, self.cfg, now)
                except AuthError as e:
                    if e.code == "unknown_key" and fetch:
                        await self.refresh_jwks(fetch)
                        ident = verify_jwt(cred, self.cfg, now)
                    else:
                        raise
            else:
                ident = verify_api_key(cred, self.cfg, now)
            if ident is None:
                raise AuthError(401, "bad_credentials", "credential not recognised")
            return ident
        except AuthError:
            self.record_failure(client_ip, now)
            raise

    def authorize(self, ident: Identity, endpoint: str) -> None:
        """Role check + MFA for privileged roles. Raises AuthError(403)."""
        if endpoint in PUBLIC or self.cfg.mode == "off" or (self.cfg.mode == "optional" and ident.method == "none"):
            return
        allowed = ENDPOINT_ROLES.get(endpoint, frozenset({"admin"}))
        roles = set(ident.roles)
        if not (roles & allowed) and "admin" not in roles:
            raise AuthError(403, "forbidden", f"role(s) {sorted(roles) or ['none']} may not use {endpoint}")
        privileged = roles & self.cfg.mfa_roles
        if privileged and ident.method == "jwt" and not ident.mfa:
            raise AuthError(403, "mfa_required", f"role {sorted(privileged)[0]} requires multi-factor authentication")
        if privileged and ident.method == "api_key":
            raise AuthError(403, "mfa_required", f"role {sorted(privileged)[0]} cannot be used with a service API key")
