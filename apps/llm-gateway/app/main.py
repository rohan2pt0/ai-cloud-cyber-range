"""AI Guardrail Gateway - an OpenAI-compatible policy enforcement point (PEP).

client -> [gateway: input rails -> detectors] -> LiteLLM (multi-cloud router with
fallbacks: Ollama -> Gemini -> Bedrock -> Azure OpenAI) -> [gateway: output rails]

Every decision is written as one JSON audit line on stdout (shipped by Promtail /
Fluent Bit to Loki/Wazuh/Sentinel), retained >=180 days per CERT-In Directions 2022.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import secrets
import sys
import time
import uuid
from collections import OrderedDict, defaultdict, deque
from contextvars import ContextVar

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from . import answering, baseline, budget, careful, guardrails, identity, killswitch, residency
from .providers import active_detectors, run_detectors

MODE = os.getenv("GUARDRAIL_MODE", "enforce")  # enforce | monitor
UPSTREAM = os.getenv("UPSTREAM_URL", "mock")  # e.g. http://litellm:4000/v1
# Must outlast the router's worst case (3 cloud rungs x 40s, then a 300s CPU-bound local model); a shorter
# gateway timeout turned a slow-but-working laptop answer into a 502.
UPSTREAM_TIMEOUT = float(os.environ.get("UPSTREAM_TIMEOUT", "480"))
UPSTREAM_KEY = os.getenv("UPSTREAM_API_KEY", "")
MAX_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
RATE_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))
# Backpressure: at most MAX_INFLIGHT model calls at once (a CPU-bound local model answers one or two at a time); a request
# waits up to QUEUE_WAIT_S for a slot, then gets a fast 503 + Retry-After instead of piling up until everything times out.
MAX_INFLIGHT = int(os.getenv("MAX_INFLIGHT", "8"))
QUEUE_WAIT_S = float(os.getenv("QUEUE_WAIT_S", "20"))
# Latency histogram buckets (ms). Averages hide the slow tail; Prometheus computes p95/p99 from these
# (histogram_quantile), and /v1/latency reports them directly.
# SLOs (Google SRE): a target and the error budget it leaves. Availability counts only failures that are OURS (the model path
# failed, or the request was shed); a policy block is the gateway working correctly. Latency counts model calls under the bar.
SLO_AVAILABILITY = float(os.getenv("SLO_AVAILABILITY", "0.99"))
SLO_LATENCY_MS = float(os.getenv("SLO_LATENCY_MS", "30000"))       # CPU laptops answer locally in tens of seconds
SLO_LATENCY_TARGET = float(os.getenv("SLO_LATENCY_TARGET", "0.95"))
LAT_BUCKETS_MS = (50, 100, 250, 500, 1000, 2500, 5000, 10000, 30000, 60000, 120000, 300000)
ALLOWED_DOMAINS = {d.strip() for d in os.getenv("ALLOWED_LINK_DOMAINS", "rbi.org.in,sebi.gov.in,cert-in.org.in").split(",") if d.strip()}
CANARIES = {c for c in os.getenv("SYSTEM_PROMPT_CANARIES", "").split(",") if c}
# Agent tool calls: the policy (allow / deny / require_approval, glob patterns) from a JSON file, else the built-in default.
def _tool_policy() -> dict:
    path = os.getenv("TOOL_POLICY_FILE", "")
    try:
        return json.loads(open(path, encoding="utf-8").read()) if path else {}
    except (OSError, ValueError):
        return {"allow": ["__invalid_policy_blocks_every_tool__"]}       # a broken policy fails closed
TOOL_POLICY = _tool_policy()

# Identity (see identity.py). A misconfigured AUTH_* setting stops the gateway at start-up rather than silently running open.
AUTH = identity.Authenticator(identity.Config.from_env())
RES = residency.Policy.from_env()          # data residency (see residency.py); off unless RESIDENCY_MODE is set

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
audit = logging.getLogger("audit")


def _product_version() -> str:
    """The SecuRAX product version: the SECURAX_VERSION env (set at build/deploy), else the
    VERSION file baked into the image, else a dev sentinel. Single source of truth = /VERSION."""
    v = os.getenv("SECURAX_VERSION")
    if v:
        return v.strip()
    for p in ("/app/VERSION", os.path.join(os.path.dirname(__file__), "..", "..", "..", "VERSION")):
        try:
            with open(p, encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            continue
    return "0.0.0-dev"


SECURAX_VERSION = _product_version()
app = FastAPI(title="AI Guardrail Gateway", version="1.0.0")

# Allow the local Guiding Map PWA (and other localhost pages) to call the gateway from the
# browser. Scoped to localhost/127.0.0.1 on any port only — never a public origin.
if os.getenv("ALLOW_LOCAL_CORS", "1") == "1":
    import re as _re

    from fastapi.middleware.cors import CORSMiddleware
    # ...plus the estate's own HTTPS names (hub.<domain>, chat.<domain>...) when the TLS edge is on: ONE configured domain, nothing wider.
    _dom = os.getenv("SECURAX_DOMAIN", "securax.localhost").strip().lower()
    _own = rf"|https://([a-z0-9-]+\.)?{_re.escape(_dom)}" if _re.fullmatch(r"[a-z0-9.-]{4,200}", _dom) else ""
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=rf"^(https?://(localhost|127\.0\.0\.1)(:\d+)?{_own})$",
        allow_methods=["*"], allow_headers=["*"],
    )

# Cross-site requests from a browser (OWASP CSRF; doc 87). CORS stops a foreign page READING an answer, not SENDING a request: a
# "simple" POST (text/plain, no preflight) from any website open on this laptop reached /v1/chat/completions, and with
# AUTH_MODE=off (the laptop default) it spent your AI keys and allowance. A browser always names the page's origin on a cross-site
# POST; command-line and server clients send none. So a write is refused when it names an origin that is neither this estate's own
# (localhost, the estate's domain) nor the address the request itself came in on (X-Forwarded-Host from the estate's nginx).
_OWN_ORIGIN = __import__("re").compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")
def _origin_ok(origin: str, host: str) -> bool:
    from urllib.parse import urlsplit
    est = os.getenv("SECURAX_DOMAIN", "securax.localhost").strip().lower()
    if _OWN_ORIGIN.match(origin):
        return True
    o = urlsplit(origin)
    oh = (o.hostname or "").lower()
    if not oh or o.scheme not in ("http", "https"):
        return False                                     # "null" (sandboxed frames, file pages) and anything odd
    if oh == est or oh.endswith("." + est):
        return True
    return bool(host) and o.netloc.lower() == host.lower()   # same origin through the estate's front door


@app.middleware("http")
async def _refuse_cross_site_writes(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin")
        host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
        if origin is not None and not _origin_ok(origin, host):
            _metrics["cross_site_refused"] += 1
            return JSONResponse(status_code=403, content={"error": {"type": "cross_site_refused",
                                "message": "A web page from another site may not use this AI gateway."}})
    return await call_next(request)


_metrics: dict[str, int] = defaultdict(int)
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _rate_limited(principal: str) -> bool:
    now, q = time.time(), _buckets[principal]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_PER_MIN:
        return True
    q.append(now)
    return False


# Tamper-evident audit (UK CAF C1.b "securing logs"; Estonia's signed, logged exchange): every event carries the hash of
# the one before it, so deleting, reordering or editing a line breaks the chain. `./securax audit verify` checks it.
_CHAIN = {"boot": secrets.token_hex(4), "seq": 0, "prev": "0" * 64}


def chain_hash(event: dict) -> str:
    return hashlib.sha256(json.dumps(event, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def _emit(event: dict) -> None:
    event.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    _CHAIN["seq"] += 1
    event["chain"] = {"boot": _CHAIN["boot"], "seq": _CHAIN["seq"], "prev": _CHAIN["prev"]}
    _CHAIN["prev"] = h = chain_hash(event)
    audit.info(json.dumps({**event, "h": h}, default=str))


_HTTP: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    """ONE pooled HTTP client for every outbound call: keep-alive connections are reused instead of a new TCP (and TLS)
    handshake per request. Each call still passes its own timeout."""
    global _HTTP
    if _HTTP is None or _HTTP.is_closed:
        _HTTP = httpx.AsyncClient(limits=httpx.Limits(max_connections=64, max_keepalive_connections=16, keepalive_expiry=30))
    return _HTTP


@app.on_event("shutdown")
async def _close_http() -> None:
    if _HTTP is not None:
        await _HTTP.aclose()
    baseline.save()                                  # keep what normal looks like across a restart


_SLOTS: asyncio.Semaphore | None = None
_SLOTS_LOOP = None
_INFLIGHT = 0


def _slots() -> asyncio.Semaphore:
    """The in-flight limit for the running event loop (a semaphore belongs to one loop; test clients start their own)."""
    global _SLOTS, _SLOTS_LOOP
    loop = asyncio.get_running_loop()
    if _SLOTS is None or _SLOTS_LOOP is not loop:
        _SLOTS, _SLOTS_LOOP = asyncio.Semaphore(max(1, MAX_INFLIGHT)), loop
    return _SLOTS


_LAT_HIST = [0] * (len(LAT_BUCKETS_MS) + 1)        # cumulative-at-render histogram counts; the last cell is +Inf
_LAT_RECENT: deque = deque(maxlen=1000)             # the last 1000 latencies, for exact p50/p95/p99 on /v1/latency
# Which model really answered (doc 83): a quiet fall from the strong model to a small local rung must be visible. Only model
# names and times are kept (never prompt or answer text), in memory, the last SERVED_WINDOW_S, at most SERVED_CAP calls.
SERVED_WINDOW_S = 24 * 3600
SERVED_CAP = 2000
_SERVED: deque = deque(maxlen=SERVED_CAP)           # (ts, requested alias, served model, weak)


def _note_served(requested: str, served: str, now: float | None = None) -> None:
    _SERVED.append((time.time() if now is None else now, requested, served, answering.weak(served)))


def _served_report(requested: str = "", now: float | None = None) -> dict:
    cut = (time.time() if now is None else now) - SERVED_WINDOW_S
    while _SERVED and _SERVED[0][0] < cut:            # oldest first: drop what fell out of the window
        _SERVED.popleft()
    rows = [e for e in _SERVED if e[0] >= cut and (not requested or e[1] == requested)]
    tally: dict[str, list] = {}
    for _ts, _asked, served, weak in rows:
        t = tally.setdefault(served, [0, weak])
        t[0] += 1
    by = sorted(({"served": k, "calls": v[0], "weak": v[1]} for k, v in tally.items()), key=lambda r: (-r["calls"], r["served"]))
    weak_n = sum(1 for e in rows if e[3])
    return {"window_h": SERVED_WINDOW_S // 3600, "calls": len(rows), "by_served": by,
            "weak_share": round(weak_n / len(rows), 3) if rows else 0.0}


def _observe_latency(ms: float) -> None:
    for i, b in enumerate(LAT_BUCKETS_MS):
        if ms <= b:
            _LAT_HIST[i] += 1
            break
    else:
        _LAT_HIST[-1] += 1
    _LAT_RECENT.append(ms)


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]


async def _fetch_json(url: str) -> dict:
    r = await _http().get(url, timeout=5)
    r.raise_for_status()
    return r.json()


async def _authn(request: Request, endpoint: str) -> identity.Identity:
    """Authenticate + authorise the caller for `endpoint`; a refusal is audited (who, from where, why) and returned as 401/403/429."""
    ip = request.client.host if request.client else "unknown"
    try:
        ident = await AUTH.authenticate(request.headers, ip, _fetch_json)
        AUTH.authorize(ident, endpoint)
        return ident
    except identity.AuthError as e:
        _metrics["auth_denied"] += 1
        _emit({"decision": "auth_denied", "endpoint": endpoint, "reason": e.code, "client_ip": ip, "category": "LLM06"})
        raise HTTPException(e.status, detail={"error": {"type": "authentication_error" if e.status == 401 else "authorization_error",
                                                        "code": e.code, "message": e.message}}) from e


_TP: ContextVar[str] = ContextVar("traceparent", default="")      # the current request's trace context, read where the upstream call is made
_TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


def _trace(request: Request) -> tuple[str, str]:
    """W3C Trace Context: keep the caller's trace id when it sent a valid `traceparent`, else start a trace; always a fresh span for this hop.
    Lets one request be followed from the browser through the gateway to the router in any OpenTelemetry-compatible tool, with no dependency."""
    m = _TRACEPARENT.match(request.headers.get("traceparent", "").strip().lower())
    trace_id = m.group(1) if m and m.group(1) != "0" * 32 else secrets.token_hex(16)
    return trace_id, secrets.token_hex(8)


def _texts(messages: list) -> list[tuple[dict, str, str]]:
    """Every text the model will read, as (holder, key, role): a plain string, and each text part of a multi-part message
    (OpenAI's [{"type": "text", "text": ...}]), so a prompt sent as parts cannot step around the rails. The user's and tools'
    words, and the system message too: chat apps put retrieved documents there, the usual road for indirect injection."""
    out = []
    for m in messages:
        if not isinstance(m, dict) or m.get("role") not in ("user", "tool", "system"):
            continue
        c = m.get("content")
        if isinstance(c, str):
            out.append((m, "content", m["role"]))
        elif isinstance(c, list):
            out += [(part, "text", m["role"]) for part in c
                    if isinstance(part, dict) and part.get("type") in ("text", "input_text") and isinstance(part.get("text"), str)]
    return out


def _findings(fs: list[guardrails.Finding]) -> list[dict]:
    return [f.__dict__ for f in fs]


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "mode": MODE, "auth": AUTH.cfg.mode, "upstream": "mock" if UPSTREAM == "mock" else "configured",
            "detectors": active_detectors()}


@app.get("/version")
async def version() -> dict:
    """Runtime version surface (SemVer). `commit` is populated when built in CI (GIT_COMMIT)."""
    return {"product": "SecuRAX", "component": "llm-gateway",
            "version": SECURAX_VERSION, "api_version": app.version,
            "commit": os.getenv("GIT_COMMIT", "unknown"),
            "build": os.getenv("SECURAX_BUILD", "")}     # e.g. "v0.1.0+74 · 21006c7": changes with every commit


_usage: dict[str, float] = defaultdict(float)     # metering for usage reports / SLA dashboards / billing


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics(request: Request) -> str:
    await _authn(request, "metrics")
    lines = ["# TYPE guardrail_events_total counter"]
    lines += [f'guardrail_events_total{{event="{k}"}} {v}' for k, v in sorted(_metrics.items())]
    lines += ["# TYPE guardrail_tokens_total counter"]
    lines += [f'guardrail_tokens_total{{kind="{k}"}} {int(_usage[f"tokens_{k}"])}' for k in ("prompt", "completion", "reasoning")]
    lines += ["# TYPE guardrail_request_latency_ms histogram"]
    cum = 0
    for b, n in zip(LAT_BUCKETS_MS, _LAT_HIST):
        cum += n
        lines.append(f'guardrail_request_latency_ms_bucket{{le="{b}"}} {cum}')
    lines += [f'guardrail_request_latency_ms_bucket{{le="+Inf"}} {cum + _LAT_HIST[-1]}',
              f"guardrail_request_latency_ms_sum {_usage['latency_ms_sum']:.0f}", f"guardrail_request_latency_ms_count {cum + _LAT_HIST[-1]}",
              "# TYPE guardrail_inflight gauge", f"guardrail_inflight {_INFLIGHT}"]
    return "\n".join(lines) + "\n"


@app.get("/v1/slo")
async def slo(request: Request) -> dict:
    """Service-level objectives since start: are we inside target, and how much error budget is left (1.0 = untouched,
    0 = spent, negative = overspent). Spend it on change; when it runs out, fix reliability before shipping features."""
    await _authn(request, "metrics")
    total, bad = int(_metrics["sli_total"]), int(_metrics["sli_bad"])
    avail = 1.0 if total == 0 else (total - bad) / total
    allowed = (1 - SLO_AVAILABILITY) * total
    v = list(_LAT_RECENT)
    fast = 1.0 if not v else sum(1 for x in v if x <= SLO_LATENCY_MS) / len(v)
    allowed_slow = (1 - SLO_LATENCY_TARGET) * len(v)
    return {
        "availability": {"target": SLO_AVAILABILITY, "actual": round(avail, 5), "requests": total, "failed": bad,
                         "budget_remaining": 1.0 if allowed == 0 else round(1 - bad / allowed, 3), "met": avail >= SLO_AVAILABILITY},
        "latency": {"target": SLO_LATENCY_TARGET, "threshold_ms": SLO_LATENCY_MS, "actual": round(fast, 5), "samples": len(v),
                    "budget_remaining": 1.0 if allowed_slow == 0 else round(1 - sum(1 for x in v if x > SLO_LATENCY_MS) / allowed_slow, 3),
                    "met": fast >= SLO_LATENCY_TARGET},
    }


@app.get("/v1/latency")
async def latency(request: Request) -> dict:
    """p50 / p95 / p99 of the last 1000 model calls, in ms. The average is shown only next to them, never alone."""
    await _authn(request, "metrics")
    v = list(_LAT_RECENT)
    return {"samples": len(v), "p50_ms": _percentile(v, 0.50), "p95_ms": _percentile(v, 0.95), "p99_ms": _percentile(v, 0.99),
            "avg_ms": round(sum(v) / len(v), 1) if v else 0.0, "inflight": _INFLIGHT, "max_inflight": MAX_INFLIGHT}


@app.post("/v1/guardrails/inspect")
async def inspect(body: dict, request: Request) -> dict:
    """Stand-alone scan endpoint used by the agent for RAG chunks and by CI tests."""
    await _authn(request, "inspect")
    text, direction = body.get("text", ""), body.get("direction", "input")
    if direction == "input":
        v = guardrails.inspect_input(text, MAX_CHARS)
    else:
        v = guardrails.inspect_output(text, ALLOWED_DOMAINS, CANARIES)
    v.findings += await run_detectors(text, direction)
    allowed = v.allowed and not any(f.severity in guardrails.BLOCKING and not f.rule.startswith("PII-")
                                    for f in v.findings)
    return {"allowed": allowed, "risk": v.risk, "text": v.text, "findings": _findings(v.findings)}


async def _call_upstream(payload: dict) -> dict:
    if UPSTREAM == "mock":
        msgs = payload.get("messages") or []
        last = (msgs[-1].get("content") if msgs and isinstance(msgs[-1], dict) else "") or ""
        return {"id": "mock", "object": "chat.completion", "model": payload.get("model", "mock"),
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": f"[mock-llm] You said: {last}"}}]}
    headers = {"Authorization": f"Bearer {UPSTREAM_KEY}"} if UPSTREAM_KEY else {}
    if _TP.get():
        headers["traceparent"] = _TP.get()
    r = await _http().post(f"{UPSTREAM.rstrip('/')}/chat/completions", json=payload, headers=headers, timeout=UPSTREAM_TIMEOUT)
    r.raise_for_status()
    return r.json()


@app.get("/readyz")
async def readyz() -> JSONResponse:
    """READINESS (vs /healthz = liveness): can this gateway actually serve a chat right now? True only when
    the model router behind it is up. Compose gates dependants on this, so nothing starts against a router
    that is still booting — the "reports healthy but every request fails / lists half the models" window
    that a fresh `./securax up` used to have (found by the sandbox, not by a unit test)."""
    if UPSTREAM == "mock":
        return JSONResponse({"ready": True, "upstream": "mock"})
    base = UPSTREAM.rstrip("/")
    base = base[:-3] if base.endswith("/v1") else base
    try:
        r = await _http().get(f"{base}/health/readiness", timeout=3)
        if r.status_code == 200:
            return JSONResponse({"ready": True})
        return JSONResponse({"ready": False, "reason": f"router returned {r.status_code}"}, status_code=503)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ready": False, "reason": f"router unreachable: {type(exc).__name__}"}, status_code=503)


async def _upstream_model_ids() -> list[str]:
    """Ask the LiteLLM router which models are actually live, so enabling a provider plugin makes
    it appear in Chat with no gateway change. Returns [] if the upstream can't be reached."""
    if UPSTREAM == "mock":
        return []
    headers = {"Authorization": f"Bearer {UPSTREAM_KEY}"} if UPSTREAM_KEY else {}
    try:
        r = await _http().get(f"{UPSTREAM.rstrip('/')}/models", headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json().get("data", [])
        return [m["id"] for m in data if isinstance(m, dict) and m.get("id")]
    except Exception:
        return []


@app.get("/v1/models")
async def models(request: Request) -> dict:
    """OpenAI-compatible model list so chat UIs (Open WebUI, AnythingLLM) can discover and select a
    model through the gateway. It mirrors the LiteLLM router's LIVE models (so a newly enabled
    provider plugin shows up automatically), and falls back to SERVED_MODELS when the router can't
    be reached. `bank-assistant` = fast default (cloud Gemini, local fallback); `-local` = sovereign."""
    await _authn(request, "models")
    ids = await _upstream_model_ids()
    if not ids:
        ids = [m.strip() for m in os.getenv("SERVED_MODELS", "bank-assistant,bank-assistant-local,builder").split(",") if m.strip()]
    # stable de-dup preserving order
    seen: set[str] = set()
    ids = [i for i in ids if not (i in seen or seen.add(i))]
    ids += careful.aliases(ids)              # `<chat model>-careful`: draft, check each claim, rewrite (app/careful.py)
    return {"object": "list",
            "data": [{"id": i, "object": "model", "created": 0, "owned_by": "securax"} for i in ids]}


def _sse_from_completion(resp: dict, chunk_chars: int = 60):
    """Re-emit a FINISHED, already-inspected completion as an OpenAI-style server-sent-event stream.

    Why not pass tokens straight through? The output rails (canary leak, secret/exfil patterns, withhold-on-
    block, detector verdicts) need the COMPLETE reply, and this gateway is fail-closed — it must never relay
    text it has not inspected. So the gateway always takes the upstream reply whole, inspects it, and only
    then streams it to the client. Chat UIs (Open WebUI streams by default) get a valid stream; the security
    guarantee is unchanged. Cost: the reply appears when complete rather than token-by-token."""
    choice = (resp.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    base = {"id": resp.get("id") or "chatcmpl-" + uuid.uuid4().hex[:12], "object": "chat.completion.chunk",
            "created": resp.get("created") or int(time.time()), "model": resp.get("model") or ""}

    def frame(delta: dict, finish: str | None = None, extra: dict | None = None) -> str:
        body = {**base, "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
        if extra:
            body.update(extra)
        return "data: " + json.dumps(body) + "\n\n"

    yield frame({"role": "assistant", "content": ""})
    content = msg.get("content") or ""
    for i in range(0, len(content), chunk_chars):
        yield frame({"content": content[i:i + chunk_chars]})
    if msg.get("tool_calls"):
        yield frame({"tool_calls": [{**tc, "index": i} for i, tc in enumerate(msg["tool_calls"])]})
    yield frame({}, choice.get("finish_reason") or "stop", {"usage": resp["usage"]} if resp.get("usage") else None)
    yield "data: [DONE]\n\n"


# Idempotency keys (the Stripe pattern): a client that retries after a timeout or a 503 sends the SAME `Idempotency-Key`,
# and gets the first answer back instead of a second model call: no double cost, and an agent never runs a tool call twice.
# Same key + different body = 422 (a bug in the client); same key while the first call still runs = 409. Kept 24 h, newest 1,000.
IDEM_TTL_S = float(os.getenv("IDEMPOTENCY_TTL_S", str(24 * 3600)))
_IDEM: "OrderedDict[str, dict]" = OrderedDict()
_IDEM_CTX: ContextVar[str] = ContextVar("idem", default="")


def _idem_purge(now: float) -> None:
    while _IDEM and (len(_IDEM) > 1000 or now - next(iter(_IDEM.values()))["t"] > IDEM_TTL_S):
        _IDEM.popitem(last=False)


@app.get("/v1/budget")
async def budget_report(request: Request) -> dict:
    """Every caller's AI allowance and spend today and this month (callers are hashed ids, never keys)."""
    await _authn(request, "metrics")
    return budget.report()


@app.get("/v1/served")
async def served_report(request: Request, model: str = "") -> dict:
    """Which model answered over the last 24 h (optionally for one requested alias), and the share a weak fallback served."""
    await _authn(request, "metrics")
    return _served_report(model)


@app.get("/v1/anomalies")
async def anomalies_report(request: Request) -> dict:
    """The last 50 unusual uses of a caller's key (doc 92): a burst, a model it never asked for, or an hour it is never active in."""
    await _authn(request, "metrics")
    return baseline.report()


def _note_behaviour(principal: str, model: str, ident: identity.Identity, req_id: str, who: dict) -> None:
    """Per-caller baseline (app/baseline.py): detection only, never blocks, never sees prompt or answer text."""
    try:
        name = ident.subject if ident.method == "api_key" else principal      # a key's name helps a person revoke it; never a JWT subject
        found = baseline.observe(principal, model, name=name)
    except Exception:  # noqa: BLE001 - a detector fault must never fail the call it watches
        _metrics["baseline_error"] += 1
        return
    for a in found:
        _metrics[f"anomaly_{a['kind']}"] += 1
        _emit({"req_id": req_id, **who, "decision": "anomaly", "kind": a["kind"], "detail": a["detail"],
               "category": "LLM10/anomalous-use"})


@app.post("/v1/chat/completions")
async def chat(request: Request, authorization: str | None = Header(default=None)):
    key = (request.headers.get("idempotency-key") or "").strip()
    if not key:
        return await _chat(request, authorization)
    if len(key) > 128:
        raise HTTPException(400, "Idempotency-Key must be at most 128 characters")
    body = hashlib.sha256(await request.body()).hexdigest()
    scope = authorization or (request.client.host if request.client else "anon")       # one caller's key never matches another's
    ck = hashlib.sha256(f"{scope}\n{key}".encode()).hexdigest()
    now = time.time()
    _idem_purge(now)
    e = _IDEM.get(ck)
    if e:
        if e["body"] != body:
            raise HTTPException(422, "this Idempotency-Key was already used with a different request body")
        if e["state"] == "pending":
            raise HTTPException(409, "a request with this Idempotency-Key is still running", headers={"Retry-After": "5"})
        await _authn(request, "chat")                       # a replay is still an authenticated, authorised call
        _metrics["idempotent_replay"] += 1
        hdr = {**e["echo"], "Idempotent-Replayed": "true"}
        if e["stream"]:
            return StreamingResponse(_sse_from_completion(e["resp"]), media_type="text/event-stream",
                                     headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", **hdr})
        return JSONResponse(e["resp"], headers=hdr)
    _IDEM[ck] = {"state": "pending", "body": body, "t": now}
    tok = _IDEM_CTX.set(ck)
    try:
        return await _chat(request, authorization)
    finally:
        _IDEM_CTX.reset(tok)
        if _IDEM.get(ck, {}).get("state") == "pending":     # failed or refused: the key is free again for a real retry
            _IDEM.pop(ck, None)


async def _chat(request: Request, authorization: str | None) -> JSONResponse:
    ident = await _authn(request, "chat")
    _metrics["sli_total"] += 1
    payload = await request.json()
    # Careful mode (app/careful.py, doc 89): the alias `<name>-careful` runs on `<name>` and asks for the check, as does the header.
    base, by_alias = careful.split_alias(str(payload.get("model") or "")) if isinstance(payload, dict) else ("", False)
    if by_alias:
        payload["model"] = base
    want_careful = careful.wanted(by_alias, request.headers)
    asked = str(payload.get("model") or "") if isinstance(payload, dict) else ""    # the alias asked for, before any reroute
    req_id = str(uuid.uuid4())
    # Authenticated callers are rate-limited and audited by their verified subject; anonymous ones (AUTH_MODE off/optional) as before.
    caller = ident.subject if ident.method != "none" else (authorization or (request.client.host if request.client else "anon"))
    principal = hashlib.sha256(caller.encode()).hexdigest()[:12]
    trace_id, span_id = _trace(request)
    who = {"principal": principal, "trace_id": trace_id, **(ident.audit() if ident.method != "none" else {}),
           "client_ip": request.client.host if request.client else "unknown"}

    _note_behaviour(principal, asked, ident, req_id, who)       # counted before any refusal, so a refused flood still shows

    if _rate_limited(principal):
        _metrics["rate_limited"] += 1
        _emit({"req_id": req_id, **who, "decision": "rate_limited", "category": "LLM10"})
        raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": "60"})

    # Human-in-command: a person stopped this model (or all AI) with `./securax ai stop`. Nothing is sent anywhere.
    stop = killswitch.stopped(payload.get("model") or "")
    if stop:
        _metrics["ai_suspended"] += 1
        _emit({"req_id": req_id, **who, "decision": "suspended", "model": payload.get("model"), "stopped": stop,
               "category": "RBI-MRM/human-in-command"})
        what = "All AI is" if stop["scope"] == "all" else f"The model '{stop['scope']}' is"
        return JSONResponse(status_code=503, headers={"Retry-After": "300"}, content={"error": {
            "type": "ai_suspended", "req_id": req_id, "stopped_by": stop.get("by"), "since": stop.get("at"),
            "message": f"{what} switched off by a person ({stop.get('reason') or 'no reason given'}). "
                       "A human handles this instead; ask the person who runs this service."}})
    # AI allowance (app/budget.py): daily and monthly tokens per caller, cloud models only by default. Agents use far more
    # tokens than chat, so a runaway loop meets a ceiling a person chose, not the provider's bill.
    over = budget.refusal(principal) if budget.counts(RES.model_zone(payload.get("model") or "")) else None
    if over:
        _metrics["budget_exhausted"] += 1
        _emit({"req_id": req_id, **who, "decision": "budget_exhausted", **over, "category": "LLM10/cost"})
        word = "today's" if over["period"] == "day" else "this month's"
        raise HTTPException(429, f"{word} AI allowance for this caller ({over['limit']:,} tokens) is used up; it resets {over['resets']}. "
                                 f"The private local model still answers, or a person can extend it: "
                                 f"./securax ai budget extend --{over['period']} --tokens N --reason \"...\"",
                            headers={"Retry-After": "3600"})

    messages = payload.get("messages", [])
    if not isinstance(messages, list) or not messages:
        raise HTTPException(400, "`messages` must be a non-empty list")
    in_findings: list[guardrails.Finding] = []
    inspected: list[tuple[dict, guardrails.Verdict]] = []
    for holder, key, role in _texts(messages):           # 1) deterministic rails first: local, no text leaves the gateway
        v = (guardrails.inspect_context(holder[key]) if role == "system" else guardrails.inspect_input(holder[key], MAX_CHARS))
        in_findings += v.findings
        inspected.append((holder, key, v))
    # 2) data residency: classify by what was found + who is asking, and decide where this may be processed BEFORE anything is sent on
    res = RES.decide(payload.get("model") or "", in_findings, ident.data_class, request.headers.get("x-data-class", ""))
    if RES.mode != "off":
        who["residency"] = res.audit()
    if res.action == "blocked":
        _metrics["residency_blocked"] += 1
        _emit({"req_id": req_id, **who, "decision": "residency_blocked", "category": "DPDP/data-localisation"})
        return JSONResponse(status_code=403, content={"error": {"type": "data_residency", "req_id": req_id,
                            "message": "Request refused: this data may not be processed where the requested model runs. " + res.reason}})
    if res.action == "rerouted":
        _metrics["residency_rerouted"] += 1
        payload["model"] = res.model
    # 3) model-based detectors, on the REDACTED text, and never a cloud detector for a class that may not leave
    for holder, key, v in inspected:
        det = await run_detectors(v.text, "input", allow=lambda n: RES.detector_allowed(res.cls, n))
        v.findings += det
        in_findings += det
        holder[key] = v.text  # redacted / normalised text goes upstream

    blocking = [f for f in in_findings if f.severity in guardrails.BLOCKING and not f.rule.startswith("PII-")]
    if blocking and MODE == "enforce":
        _metrics["blocked_input"] += 1
        _emit({"req_id": req_id, **who, "decision": "block", "stage": "input",
               "findings": _findings(in_findings)})
        # Distinguish "your prompt matched a rule" from "a model detector is OFFLINE and we are
        # fail-closed". The second is an availability problem, not a verdict on the user's text, and
        # chat UIs that only show `message` must not make it look like the prompt was malicious.
        offline = all(f.rule.startswith("DET-unavailable-") for f in blocking)
        message = ("Request blocked: a security detector is offline and the gateway is fail-closed. "
                   "Run ./securax doctor, or ./securax guard off to rely on the built-in rails only."
                   if offline else "Request blocked by AI security policy.")
        return JSONResponse(status_code=400, content={
            "error": {"type": "guardrail_violation", "req_id": req_id,
                      "reason": "detector_unavailable" if offline else "policy",
                      "message": message,
                      "rules": sorted({f.rule for f in blocking})}})

    # 4) accuracy without prompt engineering (app/answering.py, doc 89): today's date and the answer rules a careful expert
    #    would write go first in a person's conversation. Exact-format callers and chat apps' housekeeping are left alone.
    do_careful = want_careful and careful.eligible(payload, request.headers)     # decided before the rules are added
    ruled = answering.apply(payload, request.headers)
    if ruled:
        _metrics["answer_rules"] += 1

    want_stream = bool(payload.get("stream"))
    payload["stream"] = False            # always take the reply WHOLE so the output rails can inspect it
    payload.pop("stream_options", None)  # only valid on streaming calls; upstreams reject it otherwise

    out_findings: list[guardrails.Finding] = []
    calls: list[dict] = []               # one row per model call (careful mode makes up to three), for the audit line

    async def ask(body: dict, step: str) -> dict:
        """ONE model call under the same controls as any other: a slot, the upstream, the output rails, the tool policy and the
        allowance meter. The first call's failures are the request's (502/503, as before); a careful step's raise _StepFailed."""
        global _INFLIGHT
        start = time.perf_counter()
        try:
            await asyncio.wait_for(_slots().acquire(), timeout=QUEUE_WAIT_S)
        except asyncio.TimeoutError:
            _metrics["shed_overload"] += 1
            if step != "draft":
                raise _StepFailed("busy") from None
            _metrics["sli_bad"] += 1
            _emit({"req_id": req_id, **who, "decision": "shed_overload", "inflight": _INFLIGHT})
            raise HTTPException(503, "the AI models are busy; try again shortly", headers={"Retry-After": "10"}) from None
        _INFLIGHT += 1
        try:
            _TP.set(f"00-{trace_id}-{span_id}-01")
            resp = await _call_upstream(body)
        except (httpx.HTTPError, ValueError) as exc:    # ValueError: upstream sent something that is not JSON
            _metrics["upstream_error"] += 1
            _emit({"req_id": req_id, **who, "decision": "upstream_error", "step": step, "error": str(exc)[:200]})
            if step != "draft":
                raise _StepFailed("upstream") from exc
            _metrics["sli_bad"] += 1
            raise HTTPException(502, "upstream model unavailable") from exc
        finally:
            _INFLIGHT -= 1
            _slots().release()
        latency_ms = round((time.perf_counter() - start) * 1000)
        _observe_latency(latency_ms)
        if step == "draft":
            _note_served(asked, str(resp.get("model") or body.get("model") or ""))

        withheld = False
        for choice in resp.get("choices", []):
            content = choice.get("message", {}).get("content") or ""
            v = guardrails.inspect_output(content, ALLOWED_DOMAINS, CANARIES)
            v.findings += await run_detectors(content, "output", allow=lambda n: RES.detector_allowed(res.cls, n))
            out_findings.extend(v.findings)
            # Fail-closed: withhold if the deterministic output rails flagged it OR a model detector
            # (Llama Guard / Model Armor / Bedrock) or a detector-outage raised a BLOCKING finding.
            # (inspect_output set v.allowed before the detector verdicts were appended — recompute.)
            withhold = (not v.allowed) or any(
                f.severity in guardrails.BLOCKING and not f.rule.startswith("PII-") for f in v.findings)
            if withhold and MODE == "enforce":
                withheld = True
                choice["message"]["content"] = "Response withheld by AI security policy."
                choice["finish_reason"] = "content_filter"
            elif MODE == "enforce":
                choice["message"]["content"] = v.text
            tcs = choice.get("message", {}).get("tool_calls")
            if tcs:                                              # the model wants to ACT: check the tool and its arguments
                tcs, tf = guardrails.inspect_tool_calls(tcs, TOOL_POLICY, CANARIES)
                out_findings.extend(tf)
                stop = sorted({f.rule for f in tf if f.severity in guardrails.BLOCKING and not f.rule.startswith("PII-")})
                if stop and MODE == "enforce":
                    _metrics["blocked_tool_call"] += 1
                    withheld = True
                    choice["message"].pop("tool_calls", None)
                    choice["message"]["content"] = "Tool call withheld by AI security policy (" + ", ".join(stop) + ")."
                    choice["finish_reason"] = "content_filter"
        withheld_by[id(resp)] = withheld

        # The allowance counts EVERY call, careful steps included.
        u = resp.get("usage") if isinstance(resp.get("usage"), dict) else {}
        _usage["tokens_prompt"] += int(u.get("prompt_tokens") or 0)
        _usage["tokens_completion"] += int(u.get("completion_tokens") or 0)
        _usage["tokens_reasoning"] += int((u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)   # thinking the model did, inside completion
        _usage["latency_ms_sum"] += latency_ms
        _usage["latency_ms_count"] += 1
        used = int(u.get("total_tokens") or (int(u.get("prompt_tokens") or 0) + int(u.get("completion_tokens") or 0)))
        if (budget.DAY or budget.MONTH) and budget.counts(RES.model_zone(body.get("model") or "")):
            if not used:                                 # some local models report no usage: estimate (about 4 characters a token)
                text = json.dumps(body.get("messages")) + json.dumps([c.get("message", {}).get("content") for c in resp.get("choices", [])])
                used = max(1, len(text) // 4)
            for period in budget.spend(principal, used):     # soft line (80%): warn once, never block
                _metrics["budget_warning"] += 1
                _emit({"req_id": req_id, **who, "decision": "budget_warning", "period": period, "category": "LLM10/cost"})
        calls.append({"step": step, "latency_ms": latency_ms, "usage": resp.get("usage")})
        return resp

    async def careful_step(step: str, msgs: list[dict]) -> dict:
        """A careful-mode call: its new text passes the input rails, the allowance is checked again, and its answer passes the
        output rails. Any refusal is a failed step (the person then gets the draft), never a bypass."""
        prompt = msgs[-1]
        v = guardrails.inspect_input(prompt["content"], MAX_CHARS)        # the same cap: a very long draft gets draft-only
        v.findings += await run_detectors(v.text, "input", allow=lambda n: RES.detector_allowed(res.cls, n))
        in_findings.extend(v.findings)
        if MODE == "enforce" and any(f.severity in guardrails.BLOCKING and not f.rule.startswith("PII-") for f in v.findings):
            raise _StepFailed("input rails")
        prompt["content"] = v.text
        if budget.counts(RES.model_zone(payload.get("model") or "")) and budget.refusal(principal):
            raise _StepFailed("allowance")
        r = await ask({**payload, "messages": msgs}, step)
        if withheld_by.get(id(r)) and step == "check":
            raise _StepFailed("output rails")
        return r

    def said(r: dict) -> str:
        return (((r.get("choices") or [{}])[0].get("message") or {}).get("content") or "") if isinstance(r, dict) else ""

    withheld_by: dict[int, bool] = {}
    resp = await ask(payload, "draft")
    state, flagged = "", 0
    if want_careful and not do_careful:
        state = "skipped"                                    # an exact-format or tool-calling caller: left alone
    elif do_careful:
        _metrics["careful_requested"] += 1
        draft = said(resp)
        state = "draft-only"
        try:
            if not draft.strip() or withheld_by.get(id(resp)):
                raise _StepFailed("no draft to check")
            check = said(await careful_step("check", careful.check_messages(payload["messages"], draft)))
            if not careful.judged(check):
                raise _StepFailed("no verdicts")
            flagged = careful.flagged(check)
            if flagged:                                      # nothing to fix: the draft is the answer, no third call
                fin = await careful_step("rewrite", careful.rewrite_messages(payload["messages"], draft, check))
                if not said(fin).strip():
                    raise _StepFailed("empty rewrite")
                resp = fin                                   # a withheld rewrite stays withheld: the rails decide, not the draft
            state = "done"
            _metrics["careful_done"] += 1
        except _StepFailed as why:
            flagged = 0
            _metrics["careful_draft_only"] += 1
            _emit({"req_id": req_id, **who, "decision": "careful_draft_only", "reason": str(why)})
        tot = {k: sum(int((c.get("usage") or {}).get(k) or 0) for c in calls)
               for k in ("prompt_tokens", "completion_tokens", "total_tokens")}
        if len(calls) > 1 and any(tot.values()):
            resp["usage"] = tot                              # the reply reports what the whole careful pass cost
    latency_ms = sum(c["latency_ms"] for c in calls)

    for choice in resp.get("choices", []):
        if choice.get("finish_reason") == "content_filter":
            continue
        text = choice.get("message", {}).get("content") or ""
        if state == "done" and flagged:                  # the check removed or flagged claims: say so (never on JSON)
            choice["message"]["content"] = text = careful.footnote(text, flagged)
        if ruled:                                        # an answer from a small offline model says so (never on JSON)
            marked = answering.footnote(text, str(resp.get("model") or ""), payload, request.headers)
            if marked != text:
                _metrics["answer_small_model"] += 1
                choice["message"]["content"] = marked
            noted = answering.stale_note(choice["message"].get("content") or "", payload, request.headers)
            if noted != (choice["message"].get("content") or ""):
                _metrics["answer_may_be_stale"] += 1
                choice["message"]["content"] = noted

    # A request whose PII was redacted before it reached the model is NOT a plain "allow": the audit trail (and the SOC
    # reading it) must be able to tell that data was removed. (Found by the purple-team loop.)
    redacted = any(f.rule.startswith("PII-") for f in in_findings)
    decision = "allow" if not (blocking or out_findings or redacted) else ("flag" if MODE == "monitor" else "sanitise")
    _metrics[f"decision_{decision}"] += 1
    _emit({"req_id": req_id, **who, "decision": decision, "model": payload.get("model"),
           "latency_ms": latency_ms, "usage": resp.get("usage"),
           **({"careful": {"state": state, "flagged": flagged, "calls": calls}} if state else {}),
           "findings": _findings(in_findings + out_findings)})
    resp["guardrails"] = {"req_id": req_id, "decision": decision,
                          "rules": sorted({f.rule for f in in_findings + out_findings})}
    # Customer-facing AI must say it is AI (RBI MRM draft): every answer carries the disclosure, for any client to show.
    echo = {"traceparent": f"00-{trace_id}-{span_id}-01", "X-Request-ID": req_id, "X-AI-Generated": "true", **budget.headers(principal)}
    if state:
        echo["X-SecuRAX-Careful"] = state
    if _IDEM_CTX.get():
        _IDEM[_IDEM_CTX.get()] = {"state": "done", "body": _IDEM[_IDEM_CTX.get()]["body"], "t": time.time(),
                                  "resp": resp, "stream": want_stream, "echo": echo}
    if want_stream:                                      # careful or not, the finished, inspected answer is streamed
        return StreamingResponse(_sse_from_completion(resp), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", **echo})
    return JSONResponse(resp, headers=echo)


class _StepFailed(Exception):
    """A careful-mode step could not run or was refused; the person gets the draft (X-SecuRAX-Careful: draft-only)."""
