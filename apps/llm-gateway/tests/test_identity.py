"""Identity: JWT/API-key authentication, roles, MFA for privileged roles, lock-out, and an audit trail that names the caller.

RSA keys are generated and tokens signed with the `openssl` CLI so the test signs with a real, independent implementation (the gateway
itself verifies with the standard library only)."""
import asyncio
import base64
import hashlib
import hmac
import json
import logging
import shutil
import subprocess

import pytest
from app import identity as idn
from app.main import app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(shutil.which("openssl") is None, reason="needs the openssl CLI to mint test tokens")


def b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _genkey(tmp_path_factory, name):
    d = tmp_path_factory.mktemp(name)
    pem = d / "k.pem"
    subprocess.run(["openssl", "genrsa", "-out", str(pem), "2048"], check=True, capture_output=True)
    mod = subprocess.run(["openssl", "rsa", "-in", str(pem), "-noout", "-modulus"], check=True, capture_output=True, text=True).stdout
    n = bytes.fromhex(mod.strip().split("=")[1])
    return pem, {"kty": "RSA", "kid": name, "n": b64(n), "e": b64((65537).to_bytes(3, "big")), "alg": "RS256"}


@pytest.fixture(scope="module")
def keys(tmp_path_factory):
    return {"a": _genkey(tmp_path_factory, "a"), "b": _genkey(tmp_path_factory, "b")}


def mint(pem, kid, claims, alg="RS256", secret=b""):
    h = b64(json.dumps({"alg": alg, "typ": "JWT", **({"kid": kid} if kid else {})}).encode())
    p = b64(json.dumps(claims).encode())
    signing = f"{h}.{p}".encode()
    if alg == "RS256":
        sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(pem)], input=signing, check=True, capture_output=True).stdout
    elif alg == "HS256":
        sig = hmac.new(secret, signing, hashlib.sha256).digest()
    else:
        sig = b""
    return f"{h}.{p}.{b64(sig)}"


NOW = 1_800_000_000
GOOD = {"iss": "https://idp.example", "aud": "securax", "sub": "alice", "exp": NOW + 600, "roles": ["user"], "amr": ["pwd"]}


@pytest.fixture
def cfg(keys):
    c = idn.Config(mode="required", issuer="https://idp.example", audience="securax")
    c.set_jwks({"keys": [keys["a"][1]]})
    return c


def tok(keys, claims=None, **kw):
    return mint(keys["a"][0], "a", {**GOOD, **(claims or {})}, **kw)


# ---------------------------------------------------------------------------------------------------------------- JWT
def test_valid_token_yields_identity(keys, cfg):
    i = idn.verify_jwt(tok(keys), cfg, NOW)
    assert (i.subject, i.roles, i.method, i.mfa) == ("alice", ("user",), "jwt", False)


def test_nested_roles_claim_role_map_and_mfa(keys, cfg):
    cfg.roles_claim = "realm_access.roles"
    cfg.role_map = {"bank-auditor": "auditor"}
    t = tok(keys, {"realm_access": {"roles": ["bank-auditor", "offline_access"]}, "amr": ["pwd", "otp"]})
    i = idn.verify_jwt(t, cfg, NOW)
    assert i.roles == ("auditor",) and i.mfa


@pytest.mark.parametrize("what", ["tamper", "wrong_key", "alg_none", "hs256_with_public_key", "expired", "not_before", "issuer", "audience",
                                  "no_exp", "unknown_kid", "garbage"])
def test_bad_tokens_are_refused(keys, cfg, what):
    if what == "tamper":
        h, p, s = tok(keys).split(".")
        t = f"{h}.{b64(json.dumps({**GOOD, 'roles': ['admin']}).encode())}.{s}"
    elif what == "wrong_key":
        t = mint(keys["b"][0], "a", GOOD)
    elif what == "alg_none":
        t = mint(None, "a", GOOD, alg="none")
    elif what == "hs256_with_public_key":      # classic algorithm-confusion: HMAC the token with the PUBLIC key material
        t = mint(None, "a", GOOD, alg="HS256", secret=keys["a"][1]["n"].encode())
    elif what == "expired":
        t = tok(keys, {"exp": NOW - 3600})
    elif what == "not_before":
        t = tok(keys, {"nbf": NOW + 3600})
    elif what == "issuer":
        t = tok(keys, {"iss": "https://evil.example"})
    elif what == "audience":
        t = tok(keys, {"aud": "someone-else"})
    elif what == "no_exp":
        c = dict(GOOD)
        c.pop("exp")
        t = mint(keys["a"][0], "a", c)
    elif what == "unknown_kid":
        t = mint(keys["a"][0], "zzz", GOOD)
    else:
        t = "not.a.jwt"
    with pytest.raises(idn.AuthError):
        idn.verify_jwt(t, cfg, NOW)


def test_hs256_only_with_an_operator_secret(keys, cfg):
    t = mint(None, "", GOOD, alg="HS256", secret=b"s3cret")
    with pytest.raises(idn.AuthError):         # HS256 is not in the allowed algorithms
        idn.verify_jwt(t, cfg, NOW)
    cfg.algs, cfg.hs256_secret = frozenset({"RS256", "HS256"}), "s3cret"
    assert idn.verify_jwt(t, cfg, NOW).subject == "alice"
    with pytest.raises(idn.AuthError):
        idn.verify_jwt(mint(None, "", GOOD, alg="HS256", secret=b"other"), cfg, NOW)


def test_the_none_algorithm_can_never_be_configured():
    with pytest.raises(ValueError):
        idn.Config.from_env({"AUTH_MODE": "required", "OIDC_ALGS": "RS256,none", "GATEWAY_API_KEYS": "[]"})


def test_required_mode_without_any_way_to_authenticate_refuses_to_start():
    with pytest.raises(ValueError):
        idn.Config.from_env({"AUTH_MODE": "required"})
    with pytest.raises(ValueError):
        idn.Config.from_env({"AUTH_MODE": "sometimes"})


# --------------------------------------------------------------------------------------------------------------- keys
def _keycfg(**kw):
    c = idn.Config(mode="required")
    c.api_keys = [{"id": "webui", "sha256": idn.hash_key("sk-good"), "roles": ["service"], **kw}]
    return c


def test_api_key_accepts_only_the_hashed_secret():
    c = _keycfg()
    assert idn.verify_api_key("sk-good", c).subject == "key:webui"
    assert idn.verify_api_key("sk-bad", c) is None
    assert "sk-good" not in json.dumps(c.api_keys)             # only a hash is ever stored


def test_expired_api_key_is_refused():
    with pytest.raises(idn.AuthError):
        idn.verify_api_key("sk-good", _keycfg(expires="2020-01-01"), NOW)
    assert idn.verify_api_key("sk-good", _keycfg(expires="2999-01-01"), NOW)


# --------------------------------------------------------------------------------------------------- authorise + lock-out
def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_modes_off_optional_required(keys, cfg):
    off = idn.Authenticator(idn.Config(mode="off"))
    assert run(off.authenticate({}, "1.1.1.1")).method == "none"
    opt = idn.Authenticator(idn.Config(mode="optional", api_keys=_keycfg().api_keys))
    assert run(opt.authenticate({}, "1.1.1.1")).method == "none"
    with pytest.raises(idn.AuthError):                          # a WRONG credential is never silently downgraded to anonymous
        run(opt.authenticate({"authorization": "Bearer nope"}, "1.1.1.1"))
    req = idn.Authenticator(cfg)
    with pytest.raises(idn.AuthError) as e:
        run(req.authenticate({}, "1.1.1.1"))
    assert e.value.status == 401


def test_roles_gate_endpoints_and_privileged_roles_need_mfa(keys, cfg):
    a = idn.Authenticator(cfg)
    user = idn.verify_jwt(tok(keys), cfg, NOW)
    a.authorize(user, "chat")
    with pytest.raises(idn.AuthError) as e:
        a.authorize(user, "metrics")
    assert e.value.status == 403
    aud_no_mfa = idn.verify_jwt(tok(keys, {"roles": ["auditor"]}), cfg, NOW)
    with pytest.raises(idn.AuthError) as e:
        a.authorize(aud_no_mfa, "metrics")
    assert e.value.code == "mfa_required"
    a.authorize(idn.verify_jwt(tok(keys, {"roles": ["auditor"], "amr": ["pwd", "otp"]}), cfg, NOW), "metrics")
    a.authorize(user, "healthz")                                # public


def test_service_key_may_scrape_metrics_but_never_be_admin():
    c = _keycfg()
    a = idn.Authenticator(c)
    svc = idn.verify_api_key("sk-good", c)
    a.authorize(svc, "chat")
    a.authorize(svc, "metrics")
    c.api_keys[0]["roles"] = ["admin"]
    with pytest.raises(idn.AuthError) as e:
        a.authorize(idn.verify_api_key("sk-good", c), "metrics")
    assert e.value.code == "mfa_required"


def test_repeated_failures_lock_the_client_out_then_expire():
    c = _keycfg()
    c.max_failures, c.failure_window_s, c.lockout_s = 3, 60, 100
    a = idn.Authenticator(c)
    for _ in range(3):
        with pytest.raises(idn.AuthError) as e:
            run(a.authenticate({"authorization": "Bearer wrong"}, "9.9.9.9", now=NOW))
        assert e.value.status == 401
    with pytest.raises(idn.AuthError) as e:                     # now locked: even the RIGHT key is refused
        run(a.authenticate({"authorization": "Bearer sk-good"}, "9.9.9.9", now=NOW + 1))
    assert e.value.status == 429
    assert run(a.authenticate({"authorization": "Bearer sk-good"}, "8.8.8.8", now=NOW + 1)).subject == "key:webui"   # others unaffected
    assert run(a.authenticate({"authorization": "Bearer sk-good"}, "9.9.9.9", now=NOW + 101)).subject == "key:webui"   # lock expired


# --------------------------------------------------------------------------------------------- the gateway end to end
@pytest.fixture
def client(monkeypatch):
    import app.main as m
    c = _keycfg()
    c.api_keys.append({"id": "reader", "sha256": idn.hash_key("sk-user"), "roles": ["user"]})
    monkeypatch.setattr(m, "AUTH", idn.Authenticator(c))
    return TestClient(app)


BODY = {"model": "m", "messages": [{"role": "user", "content": "hello"}]}


def test_gateway_refuses_anonymous_and_audits_the_refusal(client, caplog):
    caplog.set_level(logging.INFO, logger="audit")
    r = client.post("/v1/chat/completions", json=BODY)
    assert r.status_code == 401
    ev = [json.loads(x.message) for x in caplog.records if x.name == "audit"]
    assert ev and ev[-1]["decision"] == "auth_denied" and ev[-1]["reason"] == "no_credentials" and "client_ip" in ev[-1]


def test_gateway_names_the_caller_in_the_audit_trail(client, caplog):
    caplog.set_level(logging.INFO, logger="audit")
    r = client.post("/v1/chat/completions", json=BODY, headers={"Authorization": "Bearer sk-user"})
    assert r.status_code == 200
    last = [json.loads(x.message) for x in caplog.records if x.name == "audit"][-1]
    assert last["subject"] == "key:reader" and last["roles"] == ["user"] and last["auth"] == "api_key" and last["decision"] == "allow"


def test_gateway_enforces_roles_per_endpoint(client):
    assert client.get("/metrics", headers={"Authorization": "Bearer sk-user"}).status_code == 403
    assert client.get("/metrics", headers={"Authorization": "Bearer sk-good"}).status_code == 200      # service key may scrape
    assert client.get("/healthz").status_code == 200                                                   # liveness is public
    assert client.get("/v1/models").status_code == 401
    assert client.post("/v1/guardrails/inspect", json={"text": "hi"}, headers={"Authorization": "Bearer sk-user"}).status_code == 403


def test_gateway_default_is_unchanged_open_mode():
    assert TestClient(app).post("/v1/chat/completions", json=BODY).status_code == 200
