# SecuRAX — The agents army (stealth specialist advisors)

A roster of specialist advisors you can summon on demand for a **first-draft opinion** — fast,
free, grounded in globally accepted standards — so you walk into the real professional already
prepared and ask better questions. You take the **first advice from the agent, the final advice
from a licensed human.** 80/20: the agent gets you ~80% of the way at zero cost.

## The roster (`agents/personas.py`)
| Summon | Advisor | For |
|---|---|---|
| `legal` | Legal Advisor | contracts, rights, compliance red flags (→ a licensed advocate) |
| `finance` | Personal Finance Advisor | budgeting, investing, FIRE, insurance (→ a SEBI-registered adviser) |
| `cfo` | CFO | cash flow, unit economics, fundraising (→ a CA / finance head) |
| `cto` | CTO | architecture, build-vs-buy, scaling |
| `ciso` | CISO | security strategy, RBI/ISO/NIST, zero-trust, IR |
| `tax` | Tax Advisor (India) | income tax, capital gains, regime choice (→ a CA; verify current rates) |
| `dietician` | Dietician | balanced Indian diet, macros, habits (→ a registered dietician) |
| `coach` | Fitness Coach | progression, form, recovery, band workouts |
| `chef` | Chef | quick healthy Indian meals, batch cooking |
| `event` | Event Planner | logistics, budgets, timelines, vendors |
| `intel` | Intelligence Analyst | ethical OSINT, trend analysis, self-OPSEC (lawful/defensive only) |
| `career` | Career Coach | BFSI/cyber moves, certifications, interviews |
| `engineer` | SecuRAX Engineer | proposes changes to SecuRAX itself — **the credit-saver** |

## Three principles baked in
- **Stealth.** Nothing runs in the background. An agent exists only the moment you call it.
- **Sovereign + free.** Every call goes through the estate gateway / LiteLLM, which **defaults to
  your local model (Ollama)** — so summoning an advisor costs **no Claude credits**. Offline, it
  still builds the disciplined prompt deterministically.
- **Least hallucination + never the final word.** Every agent inherits the same anti-fabrication
  contract as the Guiding Map (answer first, never invent numbers/laws/prices, say "I'm not
  certain", flag what needs verifying) **plus** a hard rule: this is a *first-draft* opinion;
  for anything binding, confirm with the named professional.

## How to summon one
**From the Guiding Map (easiest):** open the cockpit → **🤖 Ask** → tap an advisor chip
(General / Legal / Finance / CFO / CTO / CISO / Tax / Dietician / Coach / Chef / Events / Intel /
Career) → ask. Answered by your local model; the Ask tab also bundles an on-device footprint
check (Guard), the community-consensus tool (Intel) and estate launch links.

**From your AI assistant (MCP):** `list_advisors`, then
`ask_advisor(agent="ciso", question="How do I phase zero-trust at home?")`.

**From the terminal (runs on your local/free model, no Claude credits):**
```bash
./securax advisors                              # list them
./securax ask ciso "How should I phase zero-trust at home?"
./securax ask finance "Right-size my emergency fund and term cover"
```

## The credit-saver: SecuRAX enhances SecuRAX
The `engineer` agent is how you keep improving the platform **without spending Claude credits**:
```bash
./securax enhance "Add a dark-mode toggle to the portal"
```
It drafts the change on your **own local/free model** via the gateway. Pair it with **Aider** or
**Cline/Continue.dev** pointed at Ollama/LiteLLM (see [15-COST-AND-MODELS.md](15-COST-AND-MODELS.md))
to apply edits locally. Reserve Claude for the hard 20% — architecture, security, final review.

> The rule, restated: **a local model types, Claude thinks.** Your advisors and your
> self-enhancement loop run on sovereign, free compute; frontier credits are spent only where
> judgement is the bottleneck.
