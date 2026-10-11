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
import sys
import time
import uuid
from collections import defaultdict, deque

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from . import guardrails
from .providers import active_detectors, run_detectors

MODE = os.getenv("GUARDRAIL_MODE", "enforce")  # enforce | monitor
UPSTREAM = os.getenv("UPSTREAM_URL", "mock")  # e.g. http://litellm:4000/v1
UPSTREAM_KEY = os.getenv("UPSTREAM_API_KEY", "")
MAX_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
RATE_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "30"))
ALLOWED_DOMAINS = {d.strip() for d in os.getenv("ALLOWED_LINK_DOMAINS", "rbi.org.in,sebi.gov.in,cert-in.org.in").split(",") if d.strip()}
CANARIES = {c for c in os.getenv("SYSTEM_PROMPT_CANARIES", "").split(",") if c}

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


def _findings(fs: list[guardrails.Finding]) -> list[dict]:
    return [f.__dict__ for f in fs]


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "mode": MODE, "upstream": "mock" if UPSTREAM == "mock" else "configured",
            "detectors": active_detectors()}


@app.get("/version")
async def version() -> dict:
    """Runtime version surface (SemVer). `commit` is populated when built in CI (GIT_COMMIT)."""
    return {"product": "SecuRAX", "component": "llm-gateway",
            "version": SECURAX_VERSION, "api_version": app.version,
            "commit": os.getenv("GIT_COMMIT", "unknown")}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    lines = ["# TYPE guardrail_events_total counter"]
    lines += [f'guardrail_events_total{{event="{k}"}} {v}' for k, v in sorted(_metrics.items())]
    return "\n".join(lines) + "\n"


@app.post("/v1/guardrails/inspect")
async def inspect(body: dict) -> dict:
    """Stand-alone scan endpoint used by the agent for RAG chunks and by CI tests."""
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
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{UPSTREAM.rstrip('/')}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


@app.post("/v1/chat/completions")
async def chat(request: Request, authorization: str | None = Header(default=None)) -> JSONResponse:
    payload = await request.json()
    req_id = str(uuid.uuid4())
    caller = authorization or (request.client.host if request.client else "anon")
    principal = hashlib.sha256(caller.encode()).hexdigest()[:12]

    if _rate_limited(principal):
        _metrics["rate_limited"] += 1
        _emit({"req_id": req_id, "principal": principal, "decision": "rate_limited", "category": "LLM10"})
        raise HTTPException(429, "rate limit exceeded")

    messages = payload.get("messages", [])
    if not isinstance(messages, list) or not messages:
        raise HTTPException(400, "`messages` must be a non-empty list")
    in_findings: list[guardrails.Finding] = []
    for m in messages:
        if m.get("role") in ("user", "tool") and isinstance(m.get("content"), str):
            v = guardrails.inspect_input(m["content"], MAX_CHARS)
            v.findings += await run_detectors(m["content"], "input")
            in_findings += v.findings
            m["content"] = v.text  # redacted / normalised text goes upstream

    blocking = [f for f in in_findings if f.severity in guardrails.BLOCKING and not f.rule.startswith("PII-")]
    if blocking and MODE == "enforce":
        _metrics["blocked_input"] += 1
        _emit({"req_id": req_id, "principal": principal, "decision": "block", "stage": "input",
               "findings": _findings(in_findings)})
        return JSONResponse(status_code=400, content={
            "error": {"type": "guardrail_violation", "req_id": req_id,
                      "message": "Request blocked by AI security policy.",
                      "rules": sorted({f.rule for f in blocking})}})

    start = time.perf_counter()
    try:
        resp = await _call_upstream(payload)
    except httpx.HTTPError as exc:
        _metrics["upstream_error"] += 1
        _emit({"req_id": req_id, "decision": "upstream_error", "error": str(exc)[:200]})
        raise HTTPException(502, "upstream model unavailable") from exc
    latency_ms = round((time.perf_counter() - start) * 1000)

    out_findings: list[guardrails.Finding] = []
    for choice in resp.get("choices", []):
        content = choice.get("message", {}).get("content") or ""
        v = guardrails.inspect_output(content, ALLOWED_DOMAINS, CANARIES)
        v.findings += await run_detectors(content, "output")
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

    decision = "allow" if not (blocking or out_findings) else ("flag" if MODE == "monitor" else "sanitise")
    _metrics[f"decision_{decision}"] += 1
    _emit({"req_id": req_id, "principal": principal, "decision": decision, "model": payload.get("model"),
           "latency_ms": latency_ms, "usage": resp.get("usage"),
           "findings": _findings(in_findings + out_findings)})
    resp["guardrails"] = {"req_id": req_id, "decision": decision,
                          "rules": sorted({f.rule for f in in_findings + out_findings})}
    return JSONResponse(resp)
