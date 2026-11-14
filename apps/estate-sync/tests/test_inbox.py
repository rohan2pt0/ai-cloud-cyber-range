"""The SMS inbox (doc 137; threat model estate-sms-inbox): a write-only door for the phone's SMS forwarder.
Off unless configured; its own tokens, which can never read state; pinned to one user; bank senders only; never a
one-time code; long digit runs masked; bounded in size, count and rate. The Life OS reads the messages on its next sync."""
import importlib
import json

import pytest
from fastapi.testclient import TestClient

DEV, BOX, USER = "device-token-abc", "inbox-token-xyz", "me"


def _client(tmp_path, monkeypatch, **env):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", DEV)
    for k in ("SYNC_INBOX_TOKENS", "SYNC_INBOX_USER", "SYNC_INBOX_MAX", "SYNC_INBOX_PER_MINUTE"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import syncsvc.main as m
    importlib.reload(m)
    return TestClient(m.app)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, SYNC_INBOX_TOKENS=BOX, SYNC_INBOX_USER=USER) as c:
        yield c


def post(c, sender, text, tok=BOX, user=USER):
    return c.post(f"/sync/inbox/sms?user={user}", headers={"Authorization": f"Bearer {tok}"}, json={"from": sender, "text": text})


def inbox(c):
    r = c.get(f"/sync/state?user={USER}", headers={"Authorization": f"Bearer {DEV}"})
    return json.loads(r.json()["payload"]["gm_sms_inbox"]) if r.status_code == 200 else []


def test_off_unless_configured(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as c:
        assert post(c, "VM-HDFCBK", "Rs 499 spent").status_code == 503


def test_its_own_token_only_and_it_cannot_read(client):
    assert post(client, "VM-HDFCBK", "Rs 499 spent", tok=DEV).status_code == 401, "a device token is not an inbox token"
    assert post(client, "VM-HDFCBK", "Rs 499 spent", tok="wrong").status_code == 401
    assert client.get(f"/sync/state?user={USER}", headers={"Authorization": f"Bearer {BOX}"}).status_code in (401, 403), "write-only"


def test_pinned_to_one_user(client):
    assert post(client, "VM-HDFCBK", "Rs 499 spent", user="someone-else").status_code == 403


def test_a_bank_message_is_kept_and_read_by_the_device(client):
    r = post(client, "VM-HDFCBK", "Rs 499 spent on HDFC Bank Credit Card XX0202 at SWIGGY on 14-11-2026")
    assert r.status_code == 200 and r.json()["kept"]
    box = inbox(client)
    assert len(box) == 1 and box[0]["from"] == "VM-HDFCBK" and "SWIGGY" in box[0]["t"] and box[0]["at"] > 0


@pytest.mark.parametrize("sender", ["Mom", "+10000000000", "", "VERYLONGSENDERNAME-X"])
def test_not_a_bank_sender_is_dropped(client, sender):
    r = post(client, sender, "Rs 499 spent")
    assert r.status_code == 202 and not r.json()["kept"]
    assert inbox(client) == []


@pytest.mark.parametrize("text", ["123456 is your OTP for a payment of Rs 499", "Your one-time password is 4321", "Use verification code 99887"])
def test_one_time_codes_are_never_kept(client, text):
    r = post(client, "AX-ICICIB", text)
    assert r.status_code == 202 and "one-time" in r.json()["why"]
    assert inbox(client) == []


def test_long_digit_runs_are_masked(client):
    post(client, "VM-SBICRD", "Card 1234 5678 9012 used for Rs 900 at FUEL")
    t = inbox(client)[0]["t"]
    assert "1234 5678 9012" not in t and "[number removed]" in t and "Rs 900" in t


def test_bounded_by_count_and_size(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, SYNC_INBOX_TOKENS=BOX, SYNC_INBOX_USER=USER, SYNC_INBOX_MAX="3") as c:
        for i in range(5):
            post(c, "VM-HDFCBK", f"Rs {i + 1}00 spent at SHOP{i}")
        box = inbox(c)
        assert len(box) == 3 and "SHOP4" in box[-1]["t"], "the newest three are kept"
        big = c.post(f"/sync/inbox/sms?user={USER}", headers={"Authorization": f"Bearer {BOX}"}, content=b"x" * 9000)
        assert big.status_code == 413


def test_rate_limited(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch, SYNC_INBOX_TOKENS=BOX, SYNC_INBOX_USER=USER, SYNC_INBOX_PER_MINUTE="2") as c:
        assert [post(c, "VM-HDFCBK", f"Rs {i} spent").status_code for i in range(3)] == [200, 200, 429]


def test_the_device_can_clear_the_inbox_and_keeps_its_other_keys(client):
    post(client, "VM-HDFCBK", "Rs 499 spent at SWIGGY")
    h = {"Authorization": f"Bearer {DEV}"}
    st = client.get(f"/sync/state?user={USER}", headers=h).json()
    cleared = {"payload": {"gm_sms_inbox": "[]", "gm_notes": "{}"}, "meta": {"gm_sms_inbox": st["meta"]["gm_sms_inbox"] + 1, "gm_notes": 1}}
    assert client.put(f"/sync/state?user={USER}", headers=h, json=cleared).status_code == 200
    assert inbox(client) == [] and "gm_notes" in client.get(f"/sync/state?user={USER}", headers=h).json()["payload"]
