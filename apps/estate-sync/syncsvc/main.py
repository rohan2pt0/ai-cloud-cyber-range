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

Server-side per-key merge (defense-in-depth): even if two devices race or a stale
device pushes a whole blob, a field is only overwritten when the incoming copy is
NEWER by its own timestamp. Keys already stored are never silently dropped by a
device that hasn't seen them. This is strictly safer than a last-writer-wins blob
store and is fully compatible with the PWA's own client-side merge.
"""
import asyncio
import hmac
import json as _json
import os
import re
import sqlite3
import time
from contextlib import asynccontextmanager, closing

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

DB_PATH = os.environ.get("SYNC_DB_PATH", "/data/estate-sync.db")
# Daily snapshots: the last merged state of each UTC day is kept for this many days, so "no backup taken" is never a thing a human has to fix.
SNAPSHOT_DAYS = int(os.environ.get("SYNC_SNAPSHOT_DAYS", "30"))
# Reject a single blob larger than this (bytes). A healthy life-OS state is a few
# hundred KB; anything in the tens of MB is a bug or an attempt to fill the disk.
MAX_BODY = int(os.environ.get("SYNC_MAX_BODY_BYTES", str(8 * 1024 * 1024)))


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
    yield


app = FastAPI(title="SecuRAX estate-sync", docs_url=None, redoc_url=None,
              openapi_url=None, lifespan=lifespan)


def _auth(authorization: str | None) -> None:
    """Fail-closed Bearer check with constant-time compare (no token leak via timing)."""
    allowed = _tokens()
    if not allowed:
        # Unconfigured estate: refuse everything rather than serve an open store.
        raise HTTPException(503, "sync is not configured (set SYNC_TOKENS in the estate .env)")
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token or not any(hmac.compare_digest(token, a) for a in allowed):
        raise HTTPException(401, "invalid or missing device token")


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
        if not allowed or not user or len(user) > 256 or not any(hmac.compare_digest(tok, a) for a in allowed):
            await ws.close(code=4401)
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
    return {"ok": True, "configured": bool(_tokens()), "sockets": _sockets()}


# The PWA's clock anchor: a HEAD to the sync base. Its Date response header (added
# by the ASGI server) is what the client uses to correct cross-device clock skew.
@app.api_route("/sync", methods=["GET", "HEAD"])
@app.api_route("/sync/", methods=["GET", "HEAD"])
def sync_root() -> Response:
    return Response(status_code=200)


def _merge(stored: dict, s_meta: dict, inc: dict, i_meta: dict) -> tuple[dict, dict]:
    """Per-key timestamp merge. A field changes only when the incoming copy is newer."""
    out, out_meta = dict(stored), dict(s_meta)
    for k, v in inc.items():
        ts = i_meta.get(k, 0) or 0
        prev = out_meta.get(k, 0) or 0
        if k not in out or ts >= prev:
            out[k] = v
            out_meta[k] = ts or int(time.time() * 1000)
    return out, out_meta


@app.get("/sync/state")
def get_state(user: str = Query(..., min_length=1, max_length=256),
              authorization: str | None = Header(default=None)) -> JSONResponse:
    _auth(authorization)
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
                    authorization: str | None = Header(default=None)) -> JSONResponse:
    _auth(authorization)
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

    with closing(_db()) as conn:
        row = conn.execute("SELECT payload, meta FROM state WHERE user_id=?", (user,)).fetchone()
        stored = json.loads(row[0]) if row else {}
        s_meta = json.loads(row[1]) if row else {}
        merged, merged_meta = _merge(stored, s_meta, inc, i_meta)
        updated_at = body.get("updated_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
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
        conn.commit()
    await _notify(user, updated_at, str(body.get("device") or "")[:64] or None)
    return JSONResponse({"ok": True, "keys": len(merged), "updated_at": updated_at, "snapshots": snaps[0], "latest_snapshot": snaps[1]})


@app.get("/sync/snapshots")
def list_snapshots(user: str = Query(..., min_length=1, max_length=256),
                   authorization: str | None = Header(default=None)) -> JSONResponse:
    _auth(authorization)
    with closing(_db()) as conn:
        rows = conn.execute("SELECT day, payload, taken_at FROM snapshots WHERE user_id=? ORDER BY day DESC", (user,)).fetchall()
    return JSONResponse([{"day": d, "keys": len(_json.loads(p)), "bytes": len(p), "taken_at": t} for d, p, t in rows])


@app.get("/sync/snapshots/{day}")
def get_snapshot(day: str, user: str = Query(..., min_length=1, max_length=256),
                 authorization: str | None = Header(default=None)) -> JSONResponse:
    _auth(authorization)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise HTTPException(400, "day must be YYYY-MM-DD")
    with closing(_db()) as conn:
        row = conn.execute("SELECT payload, meta, taken_at FROM snapshots WHERE user_id=? AND day=?", (user, day)).fetchone()
    if not row:
        raise HTTPException(404, "no snapshot for that day")
    return JSONResponse({"payload": _json.loads(row[0]), "meta": _json.loads(row[1]), "taken_at": row[2]})
