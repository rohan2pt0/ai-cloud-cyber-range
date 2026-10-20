"""Many nodes, one Life OS (doc 86): every node that runs estate-sync keeps the same data, and any one of them can stop.

A node is any machine running the estate: the laptop, a VPS, a Mac mini, a cloud or private-cloud instance. Each one lists the
others in SYNC_PEERS and, every SYNC_PEER_INTERVAL seconds, compares its copy of each person's data with theirs. Where they differ it
pulls theirs and merges, then sends its own back. The merge is the same per-key one the devices use (main._merge): it gives the same
result in any order, any number of times, so nodes that sync in any pattern end up equal, and a node that was off simply catches
up. Nothing is a primary; there is no single copy to lose.

    SYNC_PEERS          comma-separated  URL|TOKEN  or  URL|TOKEN|pull   (URL = the other node's /sync base, e.g.
                        https://vps.tail1234.ts.net/sync; TOKEN = one of THAT node's SYNC_TOKENS; pull = take from it, never send:
                        a beta node pulls from the stable ones so a beta bug can never reach them)
    SYNC_PEER_INTERVAL  seconds between rounds (default 30)
    SYNC_NODE_NAME      how this node names itself in the other nodes' logs (default: the host name)

Standard library only (urllib). The tokens travel only in the Authorization header, never in a URL.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class Peer:
    url: str
    token: str
    pull_only: bool = False
    last: dict = field(default_factory=dict)          # the last round: when, ok, pulled, pushed, error


def parse(raw: str | None = None) -> list[Peer]:
    out = []
    for item in (os.environ.get("SYNC_PEERS", "") if raw is None else raw).split(","):
        parts = [p.strip() for p in item.split("|")]
        if len(parts) >= 2 and parts[0].startswith(("http://", "https://")) and parts[1]:
            out.append(Peer(parts[0].rstrip("/"), parts[1], len(parts) > 2 and parts[2].lower() == "pull"))
    return out


def interval() -> float:
    try:
        return max(5.0, float(os.environ.get("SYNC_PEER_INTERVAL", "30")))
    except ValueError:
        return 30.0


def node_name() -> str:
    return (os.environ.get("SYNC_NODE_NAME") or socket.gethostname())[:40]


def digest(state: dict | None) -> str:
    s = state or {}
    return hashlib.sha256(json.dumps([s.get("payload", {}), s.get("meta", {})], sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def http(method: str, url: str, token: str, body: dict | None = None, timeout: float = 15):
    """(status, parsed JSON or None). Network trouble is status 0, so one unreachable node never stops the round for the others."""
    req = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:        # noqa: S310 (a URL the operator listed)
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (OSError, ValueError):
        return 0, None


def sync_peer(peer: Peer, users: list[str], read, write, call=http) -> dict:
    """One round with one peer. read(user) -> {payload, meta} or None; write(user, payload, meta) merges into this node."""
    st, theirs = call("GET", f"{peer.url}/users", peer.token)
    if st != 200 or not isinstance(theirs, list):
        return {"ok": False, "error": f"cannot reach it (HTTP {st or 'no answer'})", "pulled": 0, "pushed": 0}
    pulled = pushed = 0
    for user in sorted(set(users) | {u for u in theirs if isinstance(u, str) and 0 < len(u) <= 256}):
        st, remote = call("GET", f"{peer.url}/state?user={urllib.request.quote(user)}", peer.token)
        if st not in (200, 404):
            return {"ok": False, "error": f"HTTP {st} reading {user}", "pulled": pulled, "pushed": pushed}
        remote = remote if st == 200 and isinstance(remote, dict) else None
        mine = read(user)
        if digest(mine) == digest(remote):
            continue                                                     # already the same: nothing to do, no ping-pong
        if remote and (remote.get("payload") or {}):
            write(user, remote.get("payload") or {}, remote.get("meta") or {})
            pulled += 1
            mine = read(user)
        if not peer.pull_only and mine and digest(mine) != digest(remote):
            st, _ = call("PUT", f"{peer.url}/state?user={urllib.request.quote(user)}", peer.token,
                         {"payload": mine.get("payload", {}), "meta": mine.get("meta", {}), "device": "node:" + node_name()})
            if st != 200:
                return {"ok": False, "error": f"HTTP {st} sending {user}", "pulled": pulled, "pushed": pushed}
            pushed += 1
    return {"ok": True, "error": "", "pulled": pulled, "pushed": pushed}


def round_once(peers: list[Peer], users, read, write, call=http) -> list[dict]:
    out = []
    for p in peers:
        r = sync_peer(p, users(), read, write, call)
        p.last = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **r}
        out.append({"peer": p.url, "pull_only": p.pull_only, **p.last})
    return out
