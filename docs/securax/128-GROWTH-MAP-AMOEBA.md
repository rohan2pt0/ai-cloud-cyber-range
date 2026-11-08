# 128 · Growth map — start as an amoeba, carry the DNA

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** The amoeba principle, made real and enforceable: the estate ships as the simplest living form (one person, no server, offline) but carries the DNA + a dormant rail to grow into its enterprise organism. ./securax evolve reads local conditions (nodes, gateway, fleet server, internal mirror, teams, stress) and shows each capability's stage, whether conditions favour growing, and the one rail to pull — safe in-box steps the estate can do itself, consequential ones behind ./securax approve. Growth map is data (governance/evolution.json); principle 'amoeba' in principles.json + AGENTS.md §0; fitness evolution-declared ratchets up the count of enterprise features that ship a rail. Seeded: hunt, crisis, wargame, gateway, evolve. Tests: test_evolve.py, test_fitness.py. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**The principle.** *Start like an amoeba with the DNA to evolve into a complex organism, which evolves automatically as
conditions — favourable or unfavourable — call for it.* Nature is the best system architect ever: a cell does not wait
to be a human before it lives, and it does not stay a cell when conditions call for more. SecuRAX is built the same way,
and this is now a core principle (`amoeba` in `governance/principles.json`, carried into every app, and in AGENTS.md §0
so every builder applies it).

What it means in practice:

- **Ship the amoeba, not the organism.** The simplest living thing that helps a real person today — one person, no
  server, offline — is what ships. Never build the enterprise organism before the amoeba is alive and used.
- **Carry the DNA.** Inside that amoeba is the full blueprint, and the **dormant rail** — the seam already built — that
  lets each part grow into its enterprise form without a rewrite.
- **Offer the simplest first, but lay every rail.** When there are options, the simplest that works is the natural first
  choice; the larger ones still get their rails, so they can self-assemble later.
- **Grow as conditions warrant — favourable and unfavourable.** More nodes, more teams, traffic north-south and
  east-west, spare resources *pull* growth; load, failure and a lost node *also* drive it — the estate falls back to the
  amoeba form under stress (no single point of failure) and regrows after. This is antifragility: stress makes the next
  form stronger.
- **Automatic where safe, approved where not.** The estate performs the safe, reversible, in-box growth steps itself;
  anything that provisions infrastructure, costs money or touches endpoints is **proposed for a human's approval**, never
  done silently.

## What you run

```bash
./securax evolve                 # the growth map: every capability, its stage, and what is ready to grow now
./securax evolve hunt            # one capability's full growth path: stages, the conditions each needs, the rail
./securax evolve --conditions    # just the conditions the estate senses right now
./securax evolve --json          # the map and conditions as data
```

`evolve` reads the estate's conditions **locally** — nothing leaves the box:

| Signal | Means |
|---|---|
| `nodes` | how many reference/sync nodes are live (1 = a lone amoeba) |
| `gateway` | a model gateway is configured (`GATEWAY_URL`) — the estate can think, not only react |
| `fleet_server` | an endpoint/fleet server is configured — a standing organism, not a one-off |
| `internal_mirror` | an internal tool registry is set (`SECURAX_HUNT_MIRROR`) — mass deploy without vendor egress |
| `teams` | more than one team/tenant uses the estate |
| `load` / `lost_node` | stress signals — outgrowing the amoeba, or falling back to it |

For each capability it shows the stage it is in, whether conditions now favour the next, and the exact rail to pull. When
nothing is ready, it says so — *right-sized for today is the goal*, not maximal.

## The growth map (DNA), declared as data

`governance/evolution.json` declares, per capability: the **amoeba** form it ships, the **stages** it can grow into, the
**conditions** (`when`) that trigger each, the **rail** already built to reach it, and a graded **actuation** (`auto` =
safe, in-box; `assisted` = behind `./securax approve`). The capabilities seeded with their rails:

- **hunt** — an offline collector on one host (amoeba) → a Velociraptor fleet with throttling (colony) → a managed,
  governed, multi-team fleet with an internal tool mirror (organism). The *same packs* run at every stage; on loss of the
  fleet server it falls back to the offline amoeba, which needs no server.
- **crisis** — one responder with the register (amoeba) → per-team owners and the chase routine (colony) → shared runs
  with SLA timers, a war-room roster and an org-governed library (organism). Every requisition item already carries its
  owning team — the rail.
- **wargame** — a lone scored tabletop (amoeba) → model-graded free text and an AI-played sender (colony) → shared
  multi-player runs rolled into the exercise programme (organism). The gateway call is already wired, dormant.
- **gateway** — a local model for one person (amoeba) → a provider ladder with failover across nodes (colony) →
  per-team metering and tenancy (organism). The ladder and kill switch are already in the config.
- **evolve** itself — a read-only map (amoeba) → the estate performing the safe auto-graded steps (colony) → org-wide
  growth governance under policy (organism). The growth mechanism declares its own growth.

## Enforced, so the DNA is never dropped

Fitness check **`evolution-declared`** makes the principle real: every capability in the growth map must name its amoeba
form, the conditions for each larger stage, and the **rail already built** to reach it, with a graded actuation — and the
count of declared rails may only **ratchet up**, never down. So a feature cannot ship an enterprise ambition with no seam
to grow into it, and the rails accumulate as the estate grows. It does not force all 50-plus components to declare at
once; it locks in the ones that have, and grows from there — amoeba-style.

## Where it fits

- **Built for one, ready for many (doc 97):** `suite.json` already says what each feature's enterprise version *adds*;
  the growth map says *how it gets there automatically* and *when*, and `evolve` shows the live readiness.
- **No single point of failure (doc 91):** every scaled-up form has the amoeba as its fallback, so growing never creates
  a new SPOF.
- **Antifragility:** unfavourable conditions drive growth too — the estate comes back from stress in a stronger form.

This is a map and a recommender, with a safe actuator for the in-box steps; it never provisions infrastructure or touches
an endpoint on its own. Growth that costs or is irreversible is always your approved decision.
