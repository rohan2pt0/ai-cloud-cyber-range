"""Many nodes, one Life OS (doc 86): nodes that sync in any pattern end up with the same data, a second round changes nothing, a
pull-only (beta) node never sends, and an unreachable node is reported without stopping the others. Uses the service's real merge."""
import importlib
import random

import pytest


@pytest.fixture()
def m(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNC_DB_PATH", str(tmp_path / "s.db"))
    monkeypatch.setenv("SYNC_TOKENS", "t")
    import syncsvc.main as main
    import syncsvc.peers as peers
    importlib.reload(peers)
    importlib.reload(main)
    return main, peers


class Node:
    """An in-memory node: its own store, merged with the service's real _merge, reachable through call()."""
    def __init__(self, main, name):
        self.main, self.name, self.store, self.up = main, name, {}, True

    def read(self, user):
        return self.store.get(user)

    def write(self, user, payload, meta):
        cur = self.store.get(user) or {"payload": {}, "meta": {}}
        p, mt = self.main._merge(cur["payload"], cur["meta"], payload, meta)
        self.store[user] = {"payload": p, "meta": mt}

    def users(self):
        return list(self.store)

    def edit(self, user, key, value, ts):
        self.write(user, {key: value}, {key: ts})


def fabric(nodes):
    """call(method, url, token, body) routed to the node named in the URL (https://<name>/sync)."""
    def call(method, url, token, body=None):
        name = url.split("/")[2]
        n = nodes[name]
        if not n.up:
            return 0, None
        path, _, q = url.split("/sync", 1)[1].partition("?")
        user = q.split("user=", 1)[1] if "user=" in q else None
        if path == "/users":
            return 200, n.users()
        if path == "/state" and method == "GET":
            return (200, n.read(user)) if n.read(user) else (404, None)
        if path == "/state" and method == "PUT":
            n.write(user, body["payload"], body["meta"])
            return 200, {"ok": True}
        return 404, None
    return call


def mesh(peers, nodes, me, pull=()):
    return [peers.Peer(f"https://{n}/sync", "t", n in pull) for n in nodes if n != me]


def test_any_number_of_nodes_converge_and_a_second_round_does_nothing(m):
    main, peers = m
    rnd = random.Random(7)
    names = ["laptop", "vps", "macmini", "aws"]
    nodes = {n: Node(main, n) for n in names}
    for i in range(200):                                       # concurrent edits everywhere, clashing keys, equal timestamps too
        nodes[rnd.choice(names)].edit(rnd.choice(["me", "kid"]), f"gm_k{rnd.randrange(12)}", f"v{i}", rnd.randrange(50))
    call = fabric(nodes)
    for _ in range(2):                                         # each node does a round with every other node, in some order
        for n in rnd.sample(names, len(names)):
            peers.round_once(mesh(peers, names, n), nodes[n].users, nodes[n].read, nodes[n].write, call)
    states = [nodes[n].store for n in names]
    assert all(s == states[0] for s in states) and states[0]
    again = peers.round_once(mesh(peers, names, "laptop"), nodes["laptop"].users, nodes["laptop"].read, nodes["laptop"].write, call)
    assert all(r["ok"] and r["pulled"] == 0 and r["pushed"] == 0 for r in again)          # equal now: no ping-pong


def test_a_beta_node_pulls_but_never_sends_and_a_dead_node_does_not_stop_the_round(m):
    main, peers = m
    nodes = {n: Node(main, n) for n in ("stable", "beta", "down")}
    nodes["stable"].edit("me", "gm_a", "from stable", 10)
    nodes["beta"].edit("me", "gm_b", "a beta experiment", 20)
    nodes["down"].up = False
    out = peers.round_once(mesh(peers, ["stable", "down"], "beta", pull=("stable",)), nodes["beta"].users, nodes["beta"].read,
                           nodes["beta"].write, fabric(nodes))
    assert nodes["beta"].store["me"]["payload"]["gm_a"] == "from stable"                    # beta got the stable data
    assert "gm_b" not in nodes["stable"].store["me"]["payload"]                             # stable never saw the beta change
    assert out[0]["ok"] and out[0]["pushed"] == 0 and not out[1]["ok"] and "cannot reach" in out[1]["error"]


def test_peers_parse_ignores_junk_and_reads_pull_only(m):
    _, peers = m
    got = peers.parse("https://a/sync|tok1, junk, ftp://x|y, https://b/sync|tok2|pull, https://c/sync|")
    assert [(p.url, p.token, p.pull_only) for p in got] == [("https://a/sync", "tok1", False), ("https://b/sync", "tok2", True)]


def test_the_service_lists_users_and_peers_only_for_a_device_token(m, monkeypatch):
    main, _ = m
    from fastapi.testclient import TestClient
    with TestClient(main.app) as c:
        c.put("/sync/state?user=me", json={"payload": {"gm_a": "1"}, "meta": {"gm_a": 1}}, headers={"Authorization": "Bearer t"})
        assert c.get("/sync/users", headers={"Authorization": "Bearer t"}).json() == ["me"]
        assert c.get("/sync/users").status_code == 401
        assert c.get("/sync/peers", headers={"Authorization": "Bearer t"}).json()["peers"] == []
