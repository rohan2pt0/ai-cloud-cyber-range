# 19 — Autonomous web research (the sovereign Manus / Clawbot)

You asked for an agent that "actually surfs the webpages from instructions," like Manus or
Clawbot — but on **your** terms: sovereign, free, and safe enough for someone who runs BFSI
security for a living. This is it: `agents/web_research/`.

Give it a task in plain English. It **plans sub-queries, searches, reads pages read-only within
an allowlist you set, and writes a cited report synthesised by your own local model** (through the
guardrail gateway — zero cloud, zero Claude credits). It is autonomous in *reading and
reasoning*; it is **never** autonomous in *acting*.

## Why this one is safe to let loose
An autonomous web agent is a well-known foot-gun (SSRF pivots, prompt injection from hostile
pages, runaway crawls, silent purchases). Every one of those is closed here:

| Risk | Control |
|---|---|
| **SSRF** — agent steered into your own services or cloud metadata | Two gates on **every hop, before the request is sent**: `is_safe_target` (http(s) only; never loopback/private/link-local/reserved IPs, `169.254.169.254`, or bare internal names) **and** a DNS-resolution check that rejects a *public* hostname whose A/AAAA record points at an internal IP (DNS-rebind). Redirects are followed manually so a `302 → 169.254.169.254` is blocked before it is ever requested. |
| **Scope creep** — reads anything, anywhere | **Allowlist, fail-closed.** No allowlist → it refuses to browse. `--open` switches to deny-list-only, deliberately. Subdomains match; look-alikes don't. |
| **Prompt injection (OWASP LLM01)** — a page says "ignore your rules" | Page text is wrapped and labelled as **untrusted data**; the system contract forbids obeying instructions found in sources and tells the model to flag injection attempts. |
| **Runaway loop / cost** | Hard budgets: `max_pages`, `max_queries`, per-fetch size + timeout. |
| **Unwanted actions** — login, buy, submit, post | **Human-in-the-loop.** Anything non-GET or whose URL/intent looks state-changing is **queued as a pending action, never executed.** |
| **robots.txt** | Respected (conservative longest-match Allow/Disallow). |
| **Hallucination** | No sources read → it says so and fabricates nothing. Every claim carries an `[n]` citation; the report ends with "Confidence & gaps". |

## Use it
```bash
# CLI (read-only, allowlist required):
GATEWAY_URL=http://localhost:8080 \
  ./securax research "best term insurance for a 35yo in India, 2026" \
    --allow irdai.gov.in --allow livemint.com --allow policybazaar.com

# open browsing (deny-list only) — deliberate:
./securax research "..." --open --deny facebook.com

# as JSON, no model (just collect + cite sources):
./securax research "..." --allow example.com --json --no-llm
```
Or from any MCP client (Claude Desktop/Code, or a local agent): call the **`web_research`** tool —
`task`, `allow="a.com,b.com"` (or `open_browsing=true`), optional `deny`, `max_pages`, `use_model`.
It returns the report, the sources, the **pending actions awaiting your approval**, and what the
rails skipped and why.

## How it's wired (sovereign + free, zero Claude credits)
- **Search** → DuckDuckGo HTML (no API key). **Fetch** → read-only `httpx` with a size cap and a
  research user-agent. **Synthesis** → your local model via the guardrail gateway (`GATEWAY_URL`,
  default `http://localhost:8080`, model `bank-assistant`).
- All three are **dependency-injected**, so the whole agent is unit-tested **offline** with fakes
  (`agents/web_research/tests/` — SSRF, allowlist, robots, budgets, injection framing, HITL
  deferral, redirect-to-internal, no-fabrication). `httpx` is only needed to actually run it live.

## Going further (opt-in, now shipped)
These expand the agent's reach/authority, so each is **off by default** and gated.

- **Render engine (JS-heavy pages).** `--render` (CLI) / `make_render_fetch(...)` renders with
  headless Chromium instead of httpx (one browser reused across the run). Needs
  `pip install -r agents/web_research/requirements-render.txt` + the bundled Chromium.
  ```bash
  ./securax research "…" --allow site.com --render
  ```
  Every request the page makes is intercepted: the **document** must pass the full SSRF + allowlist
  check, while **sub-resources** (scripts/styles/fonts from CDNs) are allowed from any *public*
  host (so the page can actually render) but internal/metadata targets are still blocked
  syntactically. **Honest caveat:** Chromium does its own DNS, so the app-layer DNS-rebind check is
  best-effort for rendered pages — the binding control is to run the agent **network-isolated** (no
  route to your internal/metadata endpoints; the estate's model/data planes are already
  `internal:true`). This is why rendering is opt-in and weaker than the default httpx path.
- **Approved-action executor (HITL writes).** The read-only agent still only *queues* state-changing
  steps; this executes ONE of them, and **only with your explicit per-action approval**:
  ```bash
  ./securax act action.json --allow shop.example --approve   # omit --approve for a dry run
  ```
  It re-validates every gate (SSRF/DNS/allowlist) at execution time, writes an **append-only audit
  trail** (`agents/web_research/.audit.jsonl`) that never records the body/headers (credentials),
  stores no secrets, and does not auto-follow redirects. There is deliberately **no MCP tool** for
  it — approval must come from a person, never a model that could self-approve.

## Still deliberately NOT built
- **A PWA button.** The capability is CLI + MCP today; a guarded estate endpoint the Guiding Map
  can call is the natural next step.
- **"Approve all" / standing write consent.** Every write is approved one at a time, on purpose.
