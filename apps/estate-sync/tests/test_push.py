"""Web push from the estate (zero-setup slice 1b; threat model estate-web-push). The estate makes its own VAPID key once
(0600, never served); only a paired device subscribes, only to its own user; only https endpoints on the browsers' push
services are kept (no SSRF); the number of devices is bounded; a message is encrypted per RFC 8291 so the push service
cannot read it, signed per RFC 8292; a device the push service no longer knows is dropped."""
import importlib
import json
import os
import stat

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient

DEV, USER = "device-token-abc", "me"
EP = "https://fcm.googleapis.com/fcm/send/fake-endpoint-one"


def _browser():
    """A stand-in browser: its own key pair and auth secret, as pushManager.subscribe makes them."""
    k = ec.generate_private_key(ec.SECP256R1())
    pub = k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return k, pub, os.urandom(16)


def _sub(push, pub, auth, ep=EP):
    return {"endpoint": ep, "keys": {"p256dh": push.b64u(pub), "auth": push.b64u(auth)}}


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", DEV)
    monkeypatch.delenv("SYNC_PUSH_KEY", raising=False)
    import syncsvc.push as push
    importlib.reload(push)
    import syncsvc.main as m
    importlib.reload(m)
    return push, m, tmp_path


def _decrypt(push, blob, ua_key, ua_pub, auth):
    """The browser's side of RFC 8291, written independently of push.encrypt."""
    salt, rs, idlen = blob[:16], int.from_bytes(blob[16:20], "big"), blob[20]
    as_pub, ct = blob[21:21 + idlen], blob[21 + idlen:]
    assert rs == 4096 and idlen == 65
    shared = ua_key.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_pub))
    ikm = push._hkdf(auth, shared, b"WebPush: info\x00" + ua_pub + as_pub, 32)
    cek = push._hkdf(salt, ikm, b"Content-Encoding: aes128gcm\x00", 16)
    nonce = push._hkdf(salt, ikm, b"Content-Encoding: nonce\x00", 12)
    pt = AESGCM(cek).decrypt(nonce, ct, None)
    assert pt.endswith(b"\x02")
    return pt[:-1]


def test_the_estate_makes_its_own_key_once_and_keeps_it_private(env):
    push, _, tmp = env
    k1 = push.public_key()
    assert len(push.unb64u(k1)) == 65
    p = tmp / "vapid.pem"
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert push.public_key() == k1                       # the same key on every call and every restart
    importlib.reload(push)
    assert push.public_key() == k1


def test_only_a_paired_device_gets_the_key_and_subscribes_for_itself(env):
    push, m, _ = env
    _, pub, auth = _browser()
    with TestClient(m.app) as c:
        assert c.get(f"/sync/push/key?user={USER}").status_code == 401
        r = c.get(f"/sync/push/key?user={USER}", headers={"Authorization": f"Bearer {DEV}"})
        assert r.status_code == 200 and "PRIVATE" not in r.text and len(push.unb64u(r.json()["key"])) == 65
        assert c.post(f"/sync/push/subscribe?user={USER}", json=_sub(push, pub, auth)).status_code == 401
        r = c.post(f"/sync/push/subscribe?user={USER}", headers={"Authorization": f"Bearer {DEV}"},
                   json={"subscription": _sub(push, pub, auth), "label": "phone"})
        assert r.status_code == 200 and r.json()["devices"] == 1
        assert [s["endpoint"] for s in push.subscriptions(USER)] == [EP]
        # the off switch: the device removes itself
        r = c.delete(f"/sync/push/subscribe?user={USER}&endpoint={EP}", headers={"Authorization": f"Bearer {DEV}"})
        assert r.json()["removed"] is True and push.subscriptions(USER) == []


@pytest.mark.parametrize("ep", ["http://fcm.googleapis.com/x", "https://evil.example/x", "https://fcm.googleapis.com.evil.example/x",
                                "https://user:pw@fcm.googleapis.com/x", "https://fcm.googleapis.com:8443/x", "https://127.0.0.1/x",
                                "https://169.254.169.254/latest", "file:///etc/passwd"])
def test_only_browser_push_services_are_accepted(env, ep):
    push, m, _ = env
    _, pub, auth = _browser()
    with pytest.raises(ValueError, match="https URL|not a browser push service"):
        push.subscribe(USER, _sub(push, pub, auth, ep))
    with TestClient(m.app) as c:
        r = c.post(f"/sync/push/subscribe?user={USER}", headers={"Authorization": f"Bearer {DEV}"}, json=_sub(push, pub, auth, ep))
        assert r.status_code == 400


def test_apple_mozilla_and_windows_endpoints_are_accepted(env):
    push, _, _ = env
    for ep in ("https://web.push.apple.com/fake", "https://updates.push.services.mozilla.com/wpush/v2/fake",
               "https://wns2-par02p.notify.windows.com/w/?token=fake"):
        assert push.endpoint_problem(ep) is None, ep


def test_bad_keys_and_oversized_bodies_are_refused(env):
    push, m, _ = env
    _, pub, auth = _browser()
    with pytest.raises(ValueError, match="wrong shape"):
        push.subscribe(USER, _sub(push, pub[:30], auth))
    with pytest.raises(ValueError, match="wrong shape"):
        push.subscribe(USER, _sub(push, pub, auth[:8]))
    with pytest.raises(ValueError):
        push.subscribe(USER, _sub(push, b"\x04" + b"\x01" * 64, auth))       # not a point on the curve
    with TestClient(m.app) as c:
        r = c.post(f"/sync/push/subscribe?user={USER}", headers={"Authorization": f"Bearer {DEV}"}, content=b"x" * 5000)
        assert r.status_code == 413


def test_devices_per_person_are_bounded(env, monkeypatch):
    push, _, _ = env
    for i in range(push.MAX_PER_USER + 5):
        _, pub, auth = _browser()
        push.subscribe(USER, _sub(push, pub, auth, f"https://fcm.googleapis.com/fcm/send/fake-{i}"))
    left = push.subscriptions(USER)
    assert len(left) == push.MAX_PER_USER
    assert "fake-0" not in json.dumps(left)                 # the oldest go first


def test_a_message_is_encrypted_for_the_device_only(env):
    push, _, _ = env
    ua_key, ua_pub, auth = _browser()
    blob = push.encrypt(b'{"title":"SecuRAX","body":"2 things need you"}', ua_pub, auth)
    assert b"need you" not in blob
    assert _decrypt(push, blob, ua_key, ua_pub, auth) == b'{"title":"SecuRAX","body":"2 things need you"}'
    other_key, _, _ = _browser()
    with pytest.raises(Exception):
        _decrypt(push, blob, other_key, ua_pub, auth)


def test_the_vapid_signature_verifies_with_the_estates_public_key(env):
    push, _, _ = env
    h = push.vapid_header(EP, now=1_800_000_000)
    t = h.split("t=")[1].split(",")[0]
    k = h.split("k=")[1]
    head, body, sig = t.split(".")
    claims = json.loads(push.unb64u(body))
    assert claims["aud"] == "https://fcm.googleapis.com" and claims["exp"] == 1_800_000_000 + 12 * 3600
    raw = push.unb64u(sig)
    pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), push.unb64u(k))
    pub.verify(encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")),
               f"{head}.{body}".encode(), ec.ECDSA(hashes.SHA256()))
    with pytest.raises(InvalidSignature):
        pub.verify(encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big")),
                   f"{head}.{body}x".encode(), ec.ECDSA(hashes.SHA256()))


def test_send_reaches_every_device_and_drops_the_gone_ones(env):
    push, _, _ = env
    devs = []
    for i in range(3):
        ua_key, pub, auth = _browser()
        ep = f"https://fcm.googleapis.com/fcm/send/fake-{i}"
        push.subscribe(USER, _sub(push, pub, auth, ep))
        devs.append((ep, ua_key, pub, auth))
    seen = {}

    def poster(ep, body, headers):
        seen[ep] = (body, headers)
        return 410 if ep.endswith("fake-2") else 201
    r = push.send("2 things need you", "SecuRAX", USER, poster=poster)
    assert r == {"sent": 2, "gone": 1, "failed": 0}
    assert len(push.subscriptions(USER)) == 2
    ep, ua_key, pub, auth = devs[0]
    body, headers = seen[ep]
    assert headers["Content-Encoding"] == "aes128gcm" and headers["Authorization"].startswith("vapid t=")
    assert json.loads(_decrypt(push, body, ua_key, pub, auth)) == {"title": "SecuRAX", "body": "2 things need you"}


def test_the_command_says_plainly_when_no_device_allowed_alerts(env, capsys):
    push, _, _ = env
    assert push.main(["send", "hello"]) == 2
    assert "Allow alerts" in capsys.readouterr().err
    assert push.main(["count"]) == 0


def test_a_redirect_is_never_followed(env):
    push, _, _ = env
    assert any(isinstance(h, push._NoRedirect) for h in push._OPENER.handlers)
    assert push._NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://169.254.169.254/") is None
