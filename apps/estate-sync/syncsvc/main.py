"""SecuRAX estate-sync — the sovereign replacement for the old cloud SaaS sync.

Your life-OS state (the Guiding Map PWA's localStorage) lives on YOUR box, in a
SQLite file on a Docker volume, reached privately over Tailscale. No third-party
SaaS, no SDK, no CDN. The PWA talks to it with plain fetch (see guiding-map/ops.js):

    WS   /sync/ws                -> live "changed" pings (first message {"token","user"})
    HEAD /sync/            -> 200 (its Date header anchors the client clock)
    GET  /sync/state?user=<id>   -> { payload:{k:v}, meta:{k:ts}, updated_at }  (404 if none)
    PUT  /sync/state?user=<id>   body { payload, meta, updated_at }             -> merged
    GET  /sync/snapshots?user=<id>        -> [{day, keys, bytes, taken_at}]  (the last SYNC_SNAPSHOT_DAYS days, newest first)
    GET  /sync/snapshots/<YYYY-MM-DD>?user=<id>  -> { payload, meta, taken_at }  (to restore a day)

Auth: Authorization: Bearer <device token>. Tokens come from SYNC_TOKENS (comma-
separated) in the estate .env — NEVER committed. Fail-closed: if no tokens are
configured the service refuses every request, so an un-configured deploy can
never become an open, world-writable data store.
Or, online (doc 85): a request that came through your Cloudflare Access gate carries a
signed token, checked here (syncsvc/access.py); it may read and write only SYNC_ACCESS_USER.
    GET  /sync/whoami            -> {user, email} for such a request (the PWA pairs itself with it)
Many nodes (doc 86, syncsvc/peers.py): SYNC_PEERS lists the other nodes; every round this node pulls and merges what differs and
sends its own back, so the laptop, a VPS, a Mac mini or a cloud instance all hold the same data and any one can stop.
    GET  /sync/users             -> [user ids]          (device token only: what a peer asks first)
    GET  /sync/peers             -> the last round with each peer

Server-side per-key merge (defense-in-depth): even if two devices race or a stale
device pushes a whole blob, a field is only overwritten when the incoming copy is
NEWER by its own timestamp. Keys already stored are never silently dropped by a
device that hasn't seen them. This is strictly safer than a last-writer-wins blob
store and is fully compatible with the PWA's own client-side merge.
"""
import asyncio
import hmac
import json as _json
import math
import os
import re
import sqlite3
import time
from contextlib import asynccontextmanager, closing

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from . import access, guard, peers

DB_PATH = os.environ.get("SYNC_DB_PATH", "/data/estate-sync.db")
# Daily snapshots: the last merged state of each UTC day is kept for this many days, so "no backup taken" is never a thing a human has to fix.
SNAPSHOT_DAYS = int(os.environ.get("SYNC_SNAPSHOT_DAYS", "30"))
# Reject a single blob larger than this (bytes). A healthy life-OS state is a few
# hundred KB; anything in the tens of MB is a bug or an attempt to fill the disk.
MAX_BODY = int(os.environ.get("SYNC_MAX_BODY_BYTES", str(8 * 1024 * 1024)))
# Doc 87: each device token (each node) may make SYNC_RATE_LIMIT requests per SYNC_RATE_WINDOW_S seconds, then gets 429 + Retry-After;
# SYNC_REFUSED_ALERT_AT refused sign-ins from one address in SYNC_REFUSED_WINDOW_S seconds write one line to refused-signins.jsonl
# next to the data, and /healthz counts the addresses over it. Nobody is locked out (syncsvc/guard.py).
LIMITER = guard.RateLimiter(guard.env_int("SYNC_RATE_LIMIT", 600), guard.env_int("SYNC_RATE_WINDOW_S", 60))
REFUSED = guard.RefusedSignins(guard.env_int("SYNC_REFUSED_ALERT_AT", 10), guard.env_int("SYNC_REFUSED_WINDOW_S", 900),
                               os.path.join(os.path.dirname(DB_PATH) or ".", "refused-signins.jsonl"))
# Behind the bundled nginx every request comes from the proxy, which writes the client's address into X-Real-IP. That header counts
# only when the direct peer is in SYNC_TRUSTED_PROXIES (default: loopback and the private Docker range); anyone else's is ignored.
TRUSTED_PROXIES = guard.trusted_proxies()


def _tokens() -> set[str]:
    """Allowed device tokens, parsed fresh so a token rotation needs only a restart."""
    raw = os.environ.get("SYNC_TOKENS", "")
    return {t.strip() for t in raw.split(",") if t.strip()}


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")       # concurrent reads during a write
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def _init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with closing(_db()) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS state ("
            " user_id TEXT PRIMARY KEY,"
            " payload TEXT NOT NULL,"
            " meta TEXT NOT NULL,"
            " updated_at TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS snapshots ("
            " user_id TEXT NOT NULL, day TEXT NOT NULL, payload TEXT NOT NULL, meta TEXT NOT NULL, taken_at TEXT,"
            " PRIMARY KEY (user_id, day))"
        )
        conn.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _init_db()
    task = asyncio.create_task(_peer_loop()) if PEERS else None
    yield
    if task:
        task.cancel()


PEERS = peers.parse()


def _read(user: str) -> dict | None:
    with closing(_db()) as conn:
        row = conn.execute("SELECT payload, meta FROM state WHERE user_id=?", (user,)).fetchone()
    return {"payload": _json.loads(row[0]), "meta": _json.loads(row[1])} if row else None


def _users() -> list[str]:
    with closing(_db()) as conn:
        return [r[0] for r in conn.execute("SELECT user_id FROM state").fetchall()]


async def _peer_loop() -> None:
    """Rounds with the other nodes, for ever. A failing node is logged in /sync/peers and retried next round; it never stops the others."""
    while True:
        changed: set[str] = set()

        def write(user, payload, meta):
            merge_write(user, payload, meta, None)
            changed.add(user)
        try:
            await asyncio.to_thread(peers.round_once, PEERS, _users, _read, write)
        except Exception as exc:                  # noqa: BLE001 - a bug in one round must not end replication
            for p in PEERS:
                p.last = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ok": False, "error": repr(exc)[:200]}
        for user in changed:                      # this node's own devices hear about what came from another node
            await _notify(user, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node")
        await asyncio.sleep(peers.interval())


app = FastAPI(title="SecuRAX estate-sync", docs_url=None, redoc_url=None,
              openapi_url=None, lifespan=lifespan)

# The store apps (doc 98): an app packaged for Android or iOS runs from its own origin (capacitor://localhost on iOS,
# https://localhost on Android), not from the estate's address, so the browser asks before it lets the app read a reply.
# Only those origins are allowed, only for the state and snapshot calls, and never with cookies: a native app always
# sends its own device token, so allowing the origin grants nothing a token does not already grant.
APP_ORIGINS = [o.strip() for o in os.environ.get("SYNC_APP_ORIGINS", "capacitor://localhost,https://localhost,http://localhost").split(",") if o.strip()]


@app.middleware("http")
async def app_origins(request: Request, call_next):
    origin = request.headers.get("origin", "")
    allowed = origin in APP_ORIGINS and request.url.path.startswith(("/sync/state", "/sync/snapshots"))
    if request.method == "OPTIONS" and allowed:
        resp = Response(status_code=204)
    else:
        resp = await call_next(request)
    if allowed:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Methods"] = "GET, PUT, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        resp.headers["Access-Control-Max-Age"] = "600"
        resp.headers["Vary"] = "Origin"
    return resp


def _limit(key: str) -> None:
    """429 with Retry-After when this token (or signed-in account) has used up its window. Keys are hashes, never the token."""
    wait = LIMITER.hit(key)
    if wait:
        raise HTTPException(429, "too many requests from this device; try again shortly",
                            headers={"Retry-After": str(max(1, math.ceil(wait)))})


def _auth(authorization: str | None, cf_jwt: str | None = None, user: str | None = None) -> None:
    """Fail-closed Bearer check with constant-time compare (no token leak via timing). A verified Access sign-in is the other way in,
    and only to its own user's data."""
    if cf_jwt and access.configured():
        try:
            email = access.verify(cf_jwt)
        except access.Denied as exc:
            raise HTTPException(401, f"sign-in not accepted: {exc}")
        if user is not None and user != access.user():
            raise HTTPException(403, "a signed-in device may sync only its own data")
        _limit("a:" + guard.token_key(email))
        return
    allowed = _tokens()
    if not allowed and access.configured():
        raise HTTPException(401, "sign in through your SecuRAX address, or use a device token")
    if not allowed:
        # Unconfigured estate: refuse everything rather than serve an open store.
        raise HTTPException(503, "sync is not configured (set SYNC_TOKENS in the estate .env)")
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token or not any(hmac.compare_digest(token, a) for a in allowed):
        raise HTTPException(401, "invalid or missing device token")
    _limit(guard.token_key(token))


def _client(conn) -> str:
    """The client address of an HTTP request or a WebSocket: X-Real-IP only from a trusted proxy (guard.client_addr)."""
    return guard.client_addr(conn.client.host if conn.client else "", conn.headers.getlist("x-real-ip"), TRUSTED_PROXIES)


@app.middleware("http")
async def count_refused(request: Request, call_next):
    """Every refused sign-in (401) counts against the client's address; the count only ever alerts, it never blocks."""
    resp = await call_next(request)
    if resp.status_code == 401:
        REFUSED.refused(_client(request))
    return resp


# ── Live change notifications (WebSocket) ─────────────────────────────────────
# Push, not poll: a device that wrote a change wakes the user's OTHER devices, which
# then pull through the normal per-key merge. The socket carries NO data, only
# {"type":"changed","updated_at":...}; correctness stays with the HTTP merge, so a
# dropped socket costs latency, never data. Auth is the first message (browsers
# cannot set headers on a WebSocket, and a token in the URL would land in logs).
# One process holds the registry (SQLite + a single worker is this service's design);
# a scaled-out deployment needs a shared bus (see docs/securax/39).
_SUBS: dict[str, set[WebSocket]] = {}
MAX_SOCKETS = int(os.environ.get("SYNC_MAX_SOCKETS", "100"))
WS_IDLE_S = float(os.environ.get("SYNC_WS_IDLE_SECONDS", "90"))


def _sockets() -> int:
    return sum(len(v) for v in _SUBS.values())


async def _notify(user: str, updated_at: str, origin: str | None) -> None:
    msg = _json.dumps({"type": "changed", "updated_at": updated_at, "origin": origin})
    for ws in list(_SUBS.get(user, ())):
        try:
            await ws.send_text(msg)
        except Exception:                      # dead peer: drop it, never fail the PUT
            _SUBS.get(user, set()).discard(ws)


@app.websocket("/sync/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await ws.accept()
    user = None
    try:
        hello = _json.loads(await asyncio.wait_for(ws.receive_text(), timeout=10))
        tok = str(hello.get("token", "")) if isinstance(hello, dict) else ""
        user = str(hello.get("user", "")) if isinstance(hello, dict) else ""
        allowed = _tokens()
        cf = ws.headers.get("cf-access-jwt-assertion")
        key = guard.token_key(tok)
        if cf and access.configured():                 # came through your Access gate: its signed token decides, for its own user only
            try:
                key = "a:" + guard.token_key(await asyncio.to_thread(access.verify, cf))
                ok = user == access.user()
            except access.Denied:
                ok = False
        else:
            ok = bool(allowed) and bool(user) and len(user) <= 256 and any(hmac.compare_digest(tok, a) for a in allowed)
        if not ok:
            user = None
            REFUSED.refused(_client(ws))
            await ws.close(code=4401)
            return
        if LIMITER.hit(key):
            user = None
            await ws.close(code=4429)
            return
        if _sockets() >= MAX_SOCKETS:
            await ws.close(code=4429)
            return
        _SUBS.setdefault(user, set()).add(ws)
        await ws.send_text(_json.dumps({"type": "ready"}))
        while True:                            # client pings keep it alive; idle ones are dropped
            await asyncio.wait_for(ws.receive_text(), timeout=WS_IDLE_S)
    except (WebSocketDisconnect, asyncio.TimeoutError, ValueError, RuntimeError):
        pass
    finally:
        if user:
            _SUBS.get(user, set()).discard(ws)
            if not _SUBS.get(user):
                _SUBS.pop(user, None)
        try:
            await ws.close()
        except Exception:
            pass


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "configured": bool(_tokens()) or access.configured(), "sockets": _sockets(),
            "refused_signin_alerts": REFUSED.over()}


@app.get("/sync/users")
def list_users(authorization: str | None = Header(default=None)) -> list[str]:
    _auth(authorization)                          # a device token only: a signed-in browser has no business listing everyone
    return _users()


@app.get("/sync/peers")
def peer_status(authorization: str | None = Header(default=None)) -> dict:
    _auth(authorization)
    return {"node": peers.node_name(), "interval_s": peers.interval(),
            "peers": [{"url": p.url, "pull_only": p.pull_only, **p.last} for p in PEERS]}


@app.get("/sync/whoami")
def whoami(cf_access_jwt_assertion: str | None = Header(default=None)) -> dict:
    """For a device that came through your Access gate: whose data it syncs. The PWA calls this once and pairs itself."""
    if not (cf_access_jwt_assertion and access.configured()):
        raise HTTPException(404, "not signed in through Cloudflare Access")
    try:
        email = access.verify(cf_access_jwt_assertion)
    except access.Denied as exc:
        raise HTTPException(401, f"sign-in not accepted: {exc}")
    return {"user": access.user(), "email": email}


# The PWA's clock anchor: a HEAD to the sync base. Its Date response header (added
# by the ASGI server) is what the client uses to correct cross-device clock skew.
@app.api_route("/sync", methods=["GET", "HEAD"])
@app.api_route("/sync/", methods=["GET", "HEAD"])
def sync_root() -> Response:
    return Response(status_code=200)


def _canon(v) -> str:
    """Tie-break key. The PWA stores strings and compares them by Unicode code point (guiding-map/ops.js cpAfter), which is exactly
    Python's str order, so phone, laptop and server pick the same winner. Non-strings (other clients) compare by canonical JSON."""
    return v if isinstance(v, str) else _json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _merge(stored: dict, s_meta: dict, inc: dict, i_meta: dict) -> tuple[dict, dict]:
    """Per-key last-writer-wins merge (an LWW register per key). A field changes only when the incoming copy is NEWER; on an exact
    timestamp tie (two devices in the same millisecond) the larger canonical value wins on every server, so the merge is commutative,
    associative and idempotent: any arrival order of the same edits converges to the same state (tests/test_sync_properties.py)."""
    out, out_meta = dict(stored), dict(s_meta)
    for k, v in inc.items():
        ts = i_meta.get(k, 0) or 0
        if k not in out:
            out[k], out_meta[k] = v, ts or int(time.time() * 1000)
            continue
        prev = out_meta.get(k, 0) or 0
        if ts > prev or (ts == prev and _canon(v) > _canon(out[k])):
            out[k], out_meta[k] = v, ts
    return out, out_meta


def _bad_meta(i_meta: dict) -> str | None:
    """Timestamps are milliseconds since 1970: finite, non-negative numbers. Anything else is refused before it can break a comparison."""
    for k, ts in i_meta.items():
        if isinstance(ts, bool) or not isinstance(ts, (int, float)) or ts != ts or ts in (float("inf"), float("-inf")) or ts < 0:
            return f"meta[{str(k)[:40]!r}] must be a timestamp in milliseconds (a non-negative number)"
    return None


@app.get("/sync/state")
def get_state(user: str = Query(..., min_length=1, max_length=256),
              authorization: str | None = Header(default=None),
              cf_access_jwt_assertion: str | None = Header(default=None)) -> JSONResponse:
    _auth(authorization, cf_access_jwt_assertion, user)
    import json
    with closing(_db()) as conn:
        row = conn.execute(
            "SELECT payload, meta, updated_at FROM state WHERE user_id=?", (user,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "no state for this user yet")
    return JSONResponse({"payload": json.loads(row[0]), "meta": json.loads(row[1]), "updated_at": row[2]})


@app.put("/sync/state")
async def put_state(request: Request,
                    user: str = Query(..., min_length=1, max_length=256),
                    authorization: str | None = Header(default=None),
                    cf_access_jwt_assertion: str | None = Header(default=None)) -> JSONResponse:
    await asyncio.to_thread(_auth, authorization, cf_access_jwt_assertion, user)   # the first sign-in fetches Cloudflare's keys
    import json
    raw = await request.body()
    if len(raw) > MAX_BODY:
        raise HTTPException(413, f"state too large (> {MAX_BODY} bytes)")
    try:
        body = json.loads(raw or b"{}")
    except ValueError:
        raise HTTPException(400, "body must be JSON")
    if not isinstance(body, dict):
        raise HTTPException(400, "body must be a JSON object")
    inc = body.get("payload") or {}
    i_meta = body.get("meta") or {}
    if not isinstance(inc, dict) or not isinstance(i_meta, dict):
        raise HTTPException(400, "payload and meta must be objects")
    bad = _bad_meta(i_meta)
    if bad:
        raise HTTPException(400, bad)

    merged, updated_at, snaps = merge_write(user, inc, i_meta, body.get("updated_at"))
    await _notify(user, updated_at, str(body.get("device") or "")[:64] or None)
    return JSONResponse({"ok": True, "keys": len(merged), "updated_at": updated_at, "snapshots": snaps[0], "latest_snapshot": snaps[1]})


def merge_write(user: str, inc: dict, i_meta: dict, updated_at: str | None) -> tuple[dict, str, tuple]:
    """Read, merge and write one user's state (and today's snapshot) atomically: safe with any number of workers or processes."""
    import json
    with closing(_db()) as conn:
        # One write lock around read -> merge -> write. Without it, two workers (or containers) that read the same row each wrote back
        # their own merge and the later one erased the earlier one's keys (a lost update: 175 of 200 keys in the concurrency test).
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT payload, meta FROM state WHERE user_id=?", (user,)).fetchone()
        stored = json.loads(row[0]) if row else {}
        s_meta = json.loads(row[1]) if row else {}
        merged, merged_meta = _merge(stored, s_meta, inc, i_meta)
        updated_at = updated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        conn.execute(
            "INSERT INTO state(user_id, payload, meta, updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload, meta=excluded.meta, updated_at=excluded.updated_at",
            (user, json.dumps(merged), json.dumps(merged_meta), updated_at),
        )
        day = time.strftime("%Y-%m-%d", time.gmtime())
        conn.execute(
            "INSERT INTO snapshots(user_id, day, payload, meta, taken_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(user_id, day) DO UPDATE SET payload=excluded.payload, meta=excluded.meta, taken_at=excluded.taken_at",
            (user, day, json.dumps(merged), json.dumps(merged_meta), updated_at),
        )
        cutoff = time.strftime("%Y-%m-%d", time.gmtime(time.time() - SNAPSHOT_DAYS * 86400))
        conn.execute("DELETE FROM snapshots WHERE user_id=? AND day < ?", (user, cutoff))
        snaps = conn.execute("SELECT COUNT(*), MAX(day) FROM snapshots WHERE user_id=?", (user,)).fetchone()
        conn.execute("COMMIT")
    return merged, updated_at, snaps


@app.get("/sync/snapshots")
def list_snapshots(user: str = Query(..., min_length=1, max_length=256),
                   authorization: str | None = Header(default=None),
                   cf_access_jwt_assertion: str | None = Header(default=None)) -> JSONResponse:
    _auth(authorization, cf_access_jwt_assertion, user)
    with closing(_db()) as conn:
        rows = conn.execute("SELECT day, payload, taken_at FROM snapshots WHERE user_id=? ORDER BY day DESC", (user,)).fetchall()
    return JSONResponse([{"day": d, "keys": len(_json.loads(p)), "bytes": len(p), "taken_at": t} for d, p, t in rows])


@app.get("/sync/snapshots/{day}")
def get_snapshot(day: str, user: str = Query(..., min_length=1, max_length=256),
                 authorization: str | None = Header(default=None),
                 cf_access_jwt_assertion: str | None = Header(default=None)) -> JSONResponse:
    _auth(authorization, cf_access_jwt_assertion, user)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise HTTPException(400, "day must be YYYY-MM-DD")
    with closing(_db()) as conn:
        row = conn.execute("SELECT payload, meta, taken_at FROM snapshots WHERE user_id=? AND day=?", (user, day)).fetchone()
    if not row:
        raise HTTPException(404, "no snapshot for that day")
    return JSONResponse({"payload": _json.loads(row[0]), "meta": _json.loads(row[1]), "taken_at": row[2]})
