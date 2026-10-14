"""AI Guardrail Gateway - an OpenAI-compatible policy enforcement point (PEP).

client -> [gateway: input rails -> detectors] -> LiteLLM (multi-cloud router with
fallbacks: Ollama -> Gemini -> Bedrock -> Azure OpenAI) -> [gateway: output rails]

Every decision is written as one JSON audit line on stdout (shipped by Promtail /
Fluent Bit to Loki/Wazuh/Sentinel), retained >=180 days per CERT-In Directions 2022.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import secrets
import sys
import time
import uuid
from collections import defaultdict, deque
from contextvars import ContextVar

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from . import guardrails, identity, residency
from .providers import active_detectors, run_detectors

MODE = os.getenv("GUARDRAIL_MODE", "enforce")  # enforce | monitor
UPSTREAM = os.getenv("UPSTREAM_URL", "mock")  # e.g. http://litellm:4000/v1
# Must outlast the router's worst case (3 cloud rungs x 40s, then a 300s CPU-bound local model); a shorter
# gateway timeout turned a slow-but-working laptop answer into a 502.
UPSTREAM_TIMEOUT = float(os.environ.get("UPSTREAM_TIMEOUT", "480"))
UPSTREAM_KEY = os.getenv("UPSTREAM_API_KEY", "")
MAX_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
RATE_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))
ALLOWED_DOMAINS = {d.strip() for d in os.getenv("ALLOWED_LINK_DOMAINS", "rbi.org.in,sebi.gov.in,cert-in.org.in").split(",") if d.strip()}
CANARIES = {c for c in os.getenv("SYSTEM_PROMPT_CANARIES", "").split(",") if c}

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
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_methods=["*"], allow_headers=["*"],
    )

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


def _emit(event: dict) -> None:
    event.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    audit.info(json.dumps(event, default=str))


async def _fetch_json(url: str) -> dict:
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.get(url)
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
            "commit": os.getenv("GIT_COMMIT", "unknown")}


_usage: dict[str, float] = defaultdict(float)     # metering for usage reports / SLA dashboards / billing


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics(request: Request) -> str:
    await _authn(request, "metrics")
    lines = ["# TYPE guardrail_events_total counter"]
    lines += [f'guardrail_events_total{{event="{k}"}} {v}' for k, v in sorted(_metrics.items())]
    lines += ["# TYPE guardrail_tokens_total counter"]
    lines += [f'guardrail_tokens_total{{kind="{k}"}} {int(_usage[f"tokens_{k}"])}' for k in ("prompt", "completion")]
    lines += ["# TYPE guardrail_request_latency_ms_sum counter", f"guardrail_request_latency_ms_sum {_usage['latency_ms_sum']:.0f}",
              "# TYPE guardrail_request_latency_ms_count counter", f"guardrail_request_latency_ms_count {int(_usage['latency_ms_count'])}"]
    return "\n".join(lines) + "\n"


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
    async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as c:
        r = await c.post(f"{UPSTREAM.rstrip('/')}/chat/completions", json=payload, headers=headers)
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
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{base}/health/readiness")
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
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{UPSTREAM.rstrip('/')}/models", headers=headers)
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


@app.post("/v1/chat/completions")
async def chat(request: Request, authorization: str | None = Header(default=None)) -> JSONResponse:
    ident = await _authn(request, "chat")
    payload = await request.json()
    req_id = str(uuid.uuid4())
    # Authenticated callers are rate-limited and audited by their verified subject; anonymous ones (AUTH_MODE off/optional) as before.
    caller = ident.subject if ident.method != "none" else (authorization or (request.client.host if request.client else "anon"))
    principal = hashlib.sha256(caller.encode()).hexdigest()[:12]
    trace_id, span_id = _trace(request)
    who = {"principal": principal, "trace_id": trace_id, **(ident.audit() if ident.method != "none" else {}),
           "client_ip": request.client.host if request.client else "unknown"}

    if _rate_limited(principal):
        _metrics["rate_limited"] += 1
        _emit({"req_id": req_id, **who, "decision": "rate_limited", "category": "LLM10"})
        raise HTTPException(429, "rate limit exceeded")

    messages = payload.get("messages", [])
    if not isinstance(messages, list) or not messages:
        raise HTTPException(400, "`messages` must be a non-empty list")
    in_findings: list[guardrails.Finding] = []
    inspected: list[tuple[dict, guardrails.Verdict]] = []
    for m in messages:                                   # 1) deterministic rails first: local, no text leaves the gateway
        if m.get("role") in ("user", "tool") and isinstance(m.get("content"), str):
            v = guardrails.inspect_input(m["content"], MAX_CHARS)
            in_findings += v.findings
            inspected.append((m, v))
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
    for m, v in inspected:
        det = await run_detectors(v.text, "input", allow=lambda n: RES.detector_allowed(res.cls, n))
        v.findings += det
        in_findings += det
        m["content"] = v.text  # redacted / normalised text goes upstream

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

    want_stream = bool(payload.get("stream"))
    payload["stream"] = False            # always take the reply WHOLE so the output rails can inspect it
    payload.pop("stream_options", None)  # only valid on streaming calls; upstreams reject it otherwise

    start = time.perf_counter()
    try:
        _TP.set(f"00-{trace_id}-{span_id}-01")
        resp = await _call_upstream(payload)
    except (httpx.HTTPError, ValueError) as exc:    # ValueError: upstream sent something that is not JSON
        _metrics["upstream_error"] += 1
        _emit({"req_id": req_id, **who, "decision": "upstream_error", "error": str(exc)[:200]})
        raise HTTPException(502, "upstream model unavailable") from exc
    latency_ms = round((time.perf_counter() - start) * 1000)

    out_findings: list[guardrails.Finding] = []
    for choice in resp.get("choices", []):
        content = choice.get("message", {}).get("content") or ""
        v = guardrails.inspect_output(content, ALLOWED_DOMAINS, CANARIES)
        v.findings += await run_detectors(content, "output", allow=lambda n: RES.detector_allowed(res.cls, n))
        out_findings += v.findings
        # Fail-closed: withhold if the deterministic output rails flagged it OR a model detector
        # (Llama Guard / Model Armor / Bedrock) or a detector-outage raised a BLOCKING finding.
        # (inspect_output set v.allowed before the detector verdicts were appended — recompute.)
        withhold = (not v.allowed) or any(
            f.severity in guardrails.BLOCKING and not f.rule.startswith("PII-") for f in v.findings)
        if withhold and MODE == "enforce":
            choice["message"]["content"] = "Response withheld by AI security policy."
            choice["finish_reason"] = "content_filter"
        elif MODE == "enforce":
            choice["message"]["content"] = v.text

    # A request whose PII was redacted before it reached the model is NOT a plain "allow": the audit trail (and the SOC
    # reading it) must be able to tell that data was removed. (Found by the purple-team loop.)
    redacted = any(f.rule.startswith("PII-") for f in in_findings)
    decision = "allow" if not (blocking or out_findings or redacted) else ("flag" if MODE == "monitor" else "sanitise")
    _metrics[f"decision_{decision}"] += 1
    u = resp.get("usage") if isinstance(resp.get("usage"), dict) else {}
    _usage["tokens_prompt"] += int(u.get("prompt_tokens") or 0)
    _usage["tokens_completion"] += int(u.get("completion_tokens") or 0)
    _usage["latency_ms_sum"] += latency_ms
    _usage["latency_ms_count"] += 1
    _emit({"req_id": req_id, **who, "decision": decision, "model": payload.get("model"),
           "latency_ms": latency_ms, "usage": resp.get("usage"),
           "findings": _findings(in_findings + out_findings)})
    resp["guardrails"] = {"req_id": req_id, "decision": decision,
                          "rules": sorted({f.rule for f in in_findings + out_findings})}
    echo = {"traceparent": f"00-{trace_id}-{span_id}-01", "X-Request-ID": req_id}
    if want_stream:
        return StreamingResponse(_sse_from_completion(resp), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", **echo})
    return JSONResponse(resp, headers=echo)
