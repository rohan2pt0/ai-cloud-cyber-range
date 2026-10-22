"""Sign-in through Cloudflare Access (doc 85): a verified token opens only the owner's data, everything else is refused, and the old
device tokens keep working. Tokens are signed with the openssl CLI, an implementation independent of the one under test."""
import base64
import importlib
import json
import shutil
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(shutil.which("openssl") is None, reason="needs the openssl CLI to sign test tokens")
TEAM, AUD, OWNER = "example-team.cloudflareaccess.com", "aud-tag-for-tests", "owner@example.invalid"


def b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


@pytest.fixture(scope="module")
def key(tmp_path_factory):
    pem = tmp_path_factory.mktemp("k") / "k.pem"
    subprocess.run(["openssl", "genrsa", "-out", str(pem), "2048"], check=True, capture_output=True)
    mod = subprocess.run(["openssl", "rsa", "-in", str(pem), "-noout", "-modulus"], check=True, capture_output=True, text=True).stdout
    jwk = {"kty": "RSA", "kid": "k1", "n": b64(bytes.fromhex(mod.strip().split("=")[1])), "e": b64((65537).to_bytes(3, "big"))}
    return pem, jwk


def mint(pem, **over):
    claims = {"iss": f"https://{TEAM}", "aud": [AUD], "email": OWNER, "exp": time.time() + 600, **over}
    h = b64(json.dumps({"alg": "RS256", "kid": "k1"}).encode())
    p = b64(json.dumps(claims).encode())
    sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(pem)], input=f"{h}.{p}".encode(), check=True, capture_output=True).stdout
    return f"{h}.{p}.{b64(sig)}"


@pytest.fixture()
def app(tmp_path, monkeypatch, key):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", "device-token-for-tests")
    monkeypatch.setenv("SYNC_ACCESS_TEAM", TEAM)
    monkeypatch.setenv("SYNC_ACCESS_AUD", AUD)
    monkeypatch.setenv("SYNC_ACCESS_EMAILS", OWNER + ", second@example.invalid")
    import syncsvc.access as a
    import syncsvc.main as m
    importlib.reload(a)
    importlib.reload(m)
    monkeypatch.setattr(a, "_fetch_keys", lambda: {"k1": key[1]})
    monkeypatch.setattr(a, "_key", lambda kid, fetch=None: {"k1": key[1]}.get(kid))
    with TestClient(m.app) as c:
        yield c


def cf(tok):
    return {"Cf-Access-Jwt-Assertion": tok}


def test_a_signed_in_device_pairs_itself_and_syncs_the_owners_data(app, key):
    tok = mint(key[0])
    assert app.get("/sync/whoami", headers=cf(tok)).json() == {"user": "me", "email": OWNER}
    assert app.put("/sync/state?user=me", json={"payload": {"gm_a": "1"}, "meta": {"gm_a": 5}}, headers=cf(tok)).status_code == 200
    # the laptop's device token sees the same data: one store, two ways in
    got = app.get("/sync/state?user=me", headers={"Authorization": "Bearer device-token-for-tests"}).json()
    assert got["payload"] == {"gm_a": "1"}


def test_forged_expired_foreign_or_unlisted_tokens_are_refused(app, key):
    bad = [mint(key[0], exp=time.time() - 3600),                       # expired
           mint(key[0], iss="https://other-team.cloudflareaccess.com"),  # another team
           mint(key[0], aud=["someone-elses-app"]),                    # another application
           mint(key[0], email="stranger@example.invalid")]             # Access let them in, but they are not on the list
    h, p, s = mint(key[0]).split(".")
    forged_claims = b64(json.dumps({"iss": f"https://{TEAM}", "aud": [AUD], "email": OWNER, "exp": time.time() + 600, "x": 1}).encode())
    bad.append(f"{h}.{forged_claims}.{s}")                              # claims changed after signing
    bad.append(b64(b'{"alg":"none"}') + "." + forged_claims + ".")      # unsigned
    for t in bad:
        assert app.get("/sync/whoami", headers=cf(t)).status_code == 401, t[:40]
        assert app.get("/sync/state?user=me", headers=cf(t)).status_code == 401


def test_a_signed_in_device_reaches_only_its_own_user(app, key):
    assert app.get("/sync/state?user=somebody-else", headers=cf(mint(key[0]))).status_code == 403


def test_without_access_settings_the_header_is_ignored_and_tokens_still_rule(tmp_path, monkeypatch, key):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", "device-token-for-tests")
    for k in ("SYNC_ACCESS_TEAM", "SYNC_ACCESS_AUD", "SYNC_ACCESS_EMAILS"):
        monkeypatch.delenv(k, raising=False)
    import syncsvc.access as a
    import syncsvc.main as m
    importlib.reload(a)
    importlib.reload(m)
    with TestClient(m.app) as c:
        assert c.get("/sync/whoami", headers=cf(mint(key[0]))).status_code == 404
        assert c.get("/sync/state?user=me", headers=cf(mint(key[0]))).status_code == 401   # no token: refused as before


def test_a_new_signing_key_is_fetched_once_and_a_fetch_failure_refuses(monkeypatch, key):
    import syncsvc.access as a
    importlib.reload(a)
    monkeypatch.setenv("SYNC_ACCESS_TEAM", TEAM)
    monkeypatch.setenv("SYNC_ACCESS_AUD", AUD)
    monkeypatch.setenv("SYNC_ACCESS_EMAILS", OWNER)
    calls = []
    assert a.verify(mint(key[0]), fetch=lambda: calls.append(1) or {"k1": key[1]}) == OWNER
    assert a.verify(mint(key[0]), fetch=lambda: calls.append(1) or {}) == OWNER and len(calls) == 1   # cached: no second fetch
    importlib.reload(a)

    def down():
        raise OSError("no network")
    with pytest.raises(a.Denied):
        a.verify(mint(key[0]), fetch=down)


def test_a_malformed_token_is_denied_not_an_error():
    import syncsvc.access as a
    for junk in ("", "abc", "a.b", "a.b.c.d", "!!.??.**"):
        with pytest.raises(a.Denied, match="well-formed"):
            a.verify(junk, fetch=lambda: {})


def test_weak_keys_and_out_of_range_signatures_never_verify(key):
    import syncsvc.access as a
    pem, jwk = key
    n, e = int.from_bytes(a._b64d(jwk["n"]), "big"), int.from_bytes(a._b64d(jwk["e"]), "big")
    msg = b"header.payload"
    sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(pem)], input=msg, check=True, capture_output=True).stdout
    assert a._rsa_verify(n, e, msg, sig)                                  # the real key and signature verify
    small = subprocess.run(["openssl", "genrsa", "1024"], check=True, capture_output=True).stdout
    mod = subprocess.run(["openssl", "rsa", "-noout", "-modulus"], input=small, check=True, capture_output=True).stdout.decode()
    assert not a._rsa_verify(int(mod.strip().split("=")[1], 16), e, msg, sig[:128])   # under 2048 bits
    assert not a._rsa_verify(n, 2, msg, sig)                                           # an even exponent
    assert not a._rsa_verify(n, 1, msg, sig)                                           # a tiny exponent
    assert not a._rsa_verify(n, e, msg, sig[1:])                                       # the wrong signature length
    k = (n.bit_length() + 7) // 8
    assert not a._rsa_verify(n, e, msg, n.to_bytes(k, "big"))                          # a signature value of n or more
