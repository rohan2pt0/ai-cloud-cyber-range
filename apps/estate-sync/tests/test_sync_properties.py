"""The sync is a small distributed system (phone + laptop + tablet, offline edits, retries). These tests hold it to the properties that
make it correct regardless of timing, without any test dependency beyond the standard library:

  * convergence: the merge is commutative, associative and idempotent, so every arrival ORDER of the same edits gives the same state
  * no lost update: concurrent writers (separate connections, as separate workers/containers would be) never drop each other's keys
  * bad input is refused (400), never a crash (500)
"""
import importlib
import itertools
import random
import threading

import pytest
from fastapi.testclient import TestClient

TOK = "test-device-token-123"


@pytest.fixture()
def m(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", TOK)
    import syncsvc.main as mod
    importlib.reload(mod)
    mod._init_db()
    return mod


def _edits(rng, devices=3, keys=4, n=6):
    """Random edits per device: (key, value, ts). Timestamps collide on purpose (same millisecond on two devices)."""
    return [[(f"k{rng.randrange(keys)}", f"d{d}-{i}-{rng.random():.3f}", rng.choice([1, 2, 2, 3, 5]) * 1000) for i in range(n)]
            for d in range(devices)]


def _apply(m, batches):
    state, meta = {}, {}
    for batch in batches:
        inc = {k: v for k, v, _ in batch}
        imeta = {k: ts for k, _, ts in batch}
        state, meta = m._merge(state, meta, inc, imeta)
    return state, meta


@pytest.mark.parametrize("seed", range(40))
def test_every_arrival_order_converges_to_the_same_state(m, seed):
    rng = random.Random(seed)
    # one PUT per edit, so the same key can arrive many times with different values and colliding timestamps
    puts = [[e] for dev in _edits(rng) for e in dev]
    results = set()
    for _ in range(30):
        order = puts[:]
        rng.shuffle(order)
        results.add(repr(sorted(_apply(m, order)[0].items())))
    assert len(results) == 1, "the final state depended on arrival order"


def test_merge_is_idempotent_and_associative(m):
    rng = random.Random(7)
    a, b, c = ([[e] for e in dev] for dev in _edits(rng))
    flat = lambda xs: [e for x in xs for e in x]  # noqa: E731
    once = _apply(m, [flat(a), flat(b), flat(c)])
    assert _apply(m, [flat(a), flat(a), flat(b), flat(c), flat(c)]) == once               # replaying a push changes nothing
    for perm in itertools.permutations([flat(a), flat(b), flat(c)]):
        assert _apply(m, list(perm))[0] == once[0]


def test_concurrent_writers_never_lose_each_others_keys(m):
    """Eight writers on their own connections, each adding its own keys at the same time (what two workers or two containers do)."""
    errors = []

    def writer(w):
        try:
            for i in range(25):
                m.merge_write("me", {f"w{w}-{i}": i}, {f"w{w}-{i}": 1000 + i}, None)
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))
    ts = [threading.Thread(target=writer, args=(w,)) for w in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errors
    import json
    import sqlite3
    row = sqlite3.connect(m.DB_PATH).execute("SELECT payload FROM state WHERE user_id='me'").fetchone()
    assert len(json.loads(row[0])) == 8 * 25, "a concurrent write was lost"


def test_a_malformed_timestamp_is_refused_not_a_crash(m):
    with TestClient(m.app) as c:
        h = {"Authorization": f"Bearer {TOK}"}
        assert c.put("/sync/state?user=me", json={"payload": {"a": 1}, "meta": {"a": 5}}, headers=h).status_code == 200
        r = c.put("/sync/state?user=me", json={"payload": {"a": 2}, "meta": {"a": "tomorrow"}}, headers=h)
        assert r.status_code == 400 and "timestamp" in r.text
        assert c.get("/sync/state?user=me", headers=h).json()["payload"] == {"a": 1}


def test_tie_break_matches_the_pwa(m):
    """Same pairs as guiding-map/tests/test20.js: on an exact tie the larger value by code point wins, on the server as on the phone."""
    for a, b in [("b", "a"), ("₹2,00,000", "₹10,000"), ("\U0001F600", "￿")]:
        for first, second in ((a, b), (b, a)):
            s, mt = m._merge({}, {}, {"k": first}, {"k": 1000})
            s, mt = m._merge(s, mt, {"k": second}, {"k": 1000})
            assert s["k"] == a
