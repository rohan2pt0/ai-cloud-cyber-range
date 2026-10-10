# SecuRAX — Global Intelligence (decide the community-proven way, before it commoditises)

You already run a powerful method by hand: open **r/CCSP**, filter **Top → All time**, read the
highest-ranked posts, spot what everyone agrees on (*Pete Zerger videos + LEARNZAPP*), and act.
You do the same with Amazon **best-seller / BIFL / high-rating** filters, with top YouTube
videos, and you bought the **Honda Activa** because it was *most-sold + best resale* — i.e.
refined over many cycles. That is **revealed preference + the wisdom of crowds + the Lindy
effect** — the same engine McKinsey/BCG sell as "the pattern across hundreds of engagements."

This module (`intel/global_intel.py`) turns that instinct into a **repeatable system** you can
point at any sphere of life — and adds the one piece the manual method misses.

## The one operator insight: two opposite regimes
Copying "Top / All-time" is only right *half* the time. The engine makes you pick the regime:

| | **REPLICATE** | **EDGE** |
|---|---|---|
| Use when | passing an exam, buying a product, a proven career path | getting in **before it becomes a commodity** (a channel, a course, a trend) |
| What "Top / All-time" means | **gold** — time-tested, low variance | a **lagging** signal — by now you're *late* |
| Evidence weighting | **older + still top = stronger** (Lindy) | **newer + rising = stronger**; stale is penalised |
| Goal | **copy** the consensus | **beat** the consensus with your unfair advantage |
| Example | CCSP: Pete Zerger + LEARNZAPP | a BFSI-cyber YouTube channel while the niche is still thin |

> This is why Warikoo / Luke Ahmad worked: they entered their niche in the **early-majority**
> window. Copying them *today* in a saturated niche is the late-majority trap. The engine flags
> exactly where a trend sits on the adoption curve so you don't arrive after the party.

## What the engine does (four steps, one call)
1. **Consensus extraction** — from the ranked items *you collected*, it surfaces what the top
   results agree on, weighting each mention by rank × score × age (per the regime above), and
   reports a confidence level and how many independent sources back it.
2. **Capability fit** — scores each opportunity against **your real profile** (skills, assets,
   your *edge* — CISSP/CISM/CCSP/BFSI/RBI context — time, capital, risk), so advice stays
   realistically implementable. Out-of-domain, high-capital plays score low on purpose.
3. **Timing (edge mode)** — estimates the diffusion-of-innovation stage (innovators → early
   adopters → … → laggard) so you enter in the rising window, not the commoditised tail.
4. **Worst-case readiness** — a Klein **pre-mortem** ("imagine it failed — why?") plus a Taleb
   **barbell** (protect the proven core, risk only a small slice on the upside) and pre-committed
   **kill-criteria**. You are always prepared for the downside.

## Anti-hallucination, by design
It **never invents rankings or trends.** It analyses only the data *you* bring and labels every
estimate as an estimate. Garbage in → it tells you the data is thin and to collect more. This is
the same honesty contract as the rest of SecuRAX ([Intelligent UX](12-INTELLIGENT-UX.md)).

## How to use it

### Option A — the Guiding-Map "Intel" tab (easiest, fully offline)
> Note: the Intel tab rejoins the unified Guiding Map cockpit in Phase 2 of the merge
> ([doc 14](14-GUIDING-MAP.md)). The MCP tool (Option B) and CLI (Option C) work today.

Open the Guiding Map (`http://localhost:8088`, or installed as an app) → **Intel**. Pick the
regime (*Copy what works* / *Get ahead*), type your goal, paste the top items you collected
(one per line, best first), and optionally the names you saw repeating. It shows the consensus
with confidence, a worst-case pre-mortem + barbell, and — in edge mode — the adoption-curve
timing. The **"Does it fit me?"** card scores any option against your stored profile, and every
decision you **save** lands in a local **Decision Log** (your compounding memory). All on-device;
nothing is sent. This tab is a faithful offline twin of `intel/global_intel.py` (the Python is
the source of truth; keep the two in sync when you change the method).

### Option B — through your AI assistant (zero setup)
With the SecuRAX MCP server connected (see `mcp/README.md`), just collect the top items and ask:

> *"Use global_intel: I want to pass CCSP. Here are the top r/CCSP all-time posts I copied: …"*

The assistant calls the `global_intel` tool and returns the consensus, your fit, timing and a
worst-case plan. Paste raw post titles/text — or, better, tell it the names you saw recurring.

### Option C — command line / the worked example
```bash
./securax intel          # runs the CCSP worked example end-to-end
```
Or directly, on your own data:
```bash
python3 intel/global_intel.py decide "Pass CCSP" \
  --items intel/examples/ccsp-reddit-top.json --mode replicate \
  --vocab "Pete Zerger,LEARNZAPP,Sybex,Mike Chapple" \
  --profile intel/examples/profile.json

python3 intel/global_intel.py decide "A side income in my niche" \
  --items my-signals.json --mode edge \
  --profile intel/examples/profile.json \
  --opportunities intel/examples/opportunities.json --volume "1,2,3,6,10,18"
```

### The input format (source-agnostic — you bring the data)
A `.json` list (or `.csv` with the same columns). Edit `intel/examples/*.json` as templates:
```json
[
  {"source": "reddit/CCSP", "rank": 1, "score": 410, "age_days": 540,
   "title": "Passed CCSP! My plan", "text": "Pete Zerger videos + LEARNZAPP ..."}
]
```
- `score` = upvotes / ratings count, `rank` = position in the Top list (1 = best),
  `age_days` = how old it is (drives the Lindy / freshness weighting).
- Edit `intel/examples/profile.json` **once** with your skills/assets/edge/constraints — no PII,
  just capabilities — and every future decision is scored against *you*.

## Where the data comes from — and the honest constraints
"Don't reinvent the wheel" and "no single point of failure" (Principles P-2/P-3) apply:

| Source | Clean way to collect | Reality check |
|---|---|---|
| **Reddit** | official API (OAuth, rate-limited; the paid tier for volume) | respect ToS & rate limits; for a one-off, just copy the Top/All-time posts |
| **YouTube** | **YouTube Data API** (free quota) — titles, views, dates | views ≈ `score`, publish date ≈ `age_days` |
| **Amazon.in** | no clean public ratings API (PA-API needs an affiliate + sales) | use best-seller / rating / BIFL filters manually; record the numbers |
| **Google Trends / search** | `volume_series` for edge-mode timing | relative interest, good enough for stage estimation |

The engine is deliberately **offline and BYO-data**: no scraper to get you rate-limited or
banned, no API key required to work, nothing leaves your machine. Automated pulls (via official
APIs, through the n8n "glue" in [Integrations](07-INTEGRATIONS.md)) are an *optional* convenience
that feed the same JSON format — never a dependency.

## Why this is the right kind of "super-intelligence"
You are not outsourcing judgement — you are **standardising the best collective evidence,
filtered through your own edge, with the downside pre-planned.** That is exactly how durable
institutions decide: proven defaults, measured timing, and a plan for the worst case. Point it
at certifications, purchases, tools, career moves, side income — anywhere a crowd has already
paid the tuition of trial and error, so you don't have to.
