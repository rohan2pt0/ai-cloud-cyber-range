# 57 · Compute, memory and storage: the smart way round the limits (global and Indian options)

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟡 Partly built.** 8-bit context cache and the Indian rung are built; the rest is guidance. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**Situation:** a 16 GB laptop with no GPU that Docker can use, inside WSL/Docker, beside a full estate. The bottleneck is memory for
local models, not storage or CPU.

**What actually needs compute:**

| Work | How heavy | Needs a GPU? |
|---|---|---|
| Daily chat | short, many times a day | no; cloud rungs and the router already handle it |
| Building SecuRAX | bursts | no; the build chain's free/cheap rungs |
| Private (Red-tier) questions | must stay local | memory, not a GPU |
| Occasional heavy jobs (embedding years of chats, an autobench on bigger models, a small fine-tune) | hours, rarely | yes, for a few hours |

## 1. Built in this change

| Change | Effect | Where |
|---|---|---|
| **Context memory at half price**: Ollama keeps the conversation cache in 8-bit (`OLLAMA_KV_CACHE_TYPE=q8_0`, with flash attention) | about half the context memory of the default 16-bit, so the same RAM holds a longer conversation or a bigger model. A model that cannot use it falls back by itself; `OLLAMA_KV_CACHE_TYPE=f16` switches back | `docker-compose.yml` (ollama) |
| **Indian cloud rung `e2e-in`** (E2E Networks TIR): OpenAI-compatible GenAI API, GPUs in Indian data centres, INR invoices, paid, **opt-in, in no chain** | an in-country option for when residency matters | `./securax providers add e2e_tir` (key + the base URL from the TIR console) |
| **The home rung** (doc 56): lend the estate your own stronger machine over Tailscale | the biggest single win if you have, or buy, one good box | `REMOTE_OLLAMA_BASE`, `HOME_MODEL` |

**The Indian rung's residency zone is not assumed.** E2E's docs say its GPUs are in India, but I found no statement that GenAI API
requests stay in India. Until E2E confirms it in writing, `e2e-in` is treated as zone `global` (fail-closed). After confirmation, add
`"e2e-in": "in"` to `model_zones` in `governance/residency/IN.json`. From then on, confidential data may be routed there under
`./securax residency enable`.

## 2. The options, ranked for you

### Do (best value)

1. **A home machine** (doc 56). A Mac mini M4 with 24 GB unified memory (about ₹91,000–1,00,000 from major Indian retailers in
   2026; check before buying) runs a 14–20B model at chat speed. It idles at a few watts, so it can stay on all day, and it becomes
   your `home` rung. This is the RAMDeck benefit without the risk. Never use the bank-issued laptop for this.
2. **Cloud rungs for daily work, local for private work.** This is already how the chains work: free and cheap rungs first,
   `home` and local last, residency keeping Red-tier local.
3. **8-bit context cache** (built above), and `./securax profile` so the estate fits the RAM WSL gives Docker
   (`.wslconfig memory=`).

### Use for heavy one-off jobs (Green-tier data only)

| Option | What it is good for | Watch out for |
|---|---|---|
| **Kaggle Notebooks** (free; T4/P100 GPUs, TPU v3-8, weekly quotas) | batch jobs: embed your exported chats, run an autobench on bigger models, a small fine-tune | Your data goes to Google, so only Green-tier. Sessions end (9–12 h), so it is **not** an always-on endpoint. Tunnelling a server out of a notebook is a grey area in the terms; I could not find the current wording, so don't build on it |
| **Google Colab** | the same | the same; plus the old doc-22 tunnel recipe is now marked experiment-only |
| **Lightning AI / Paperspace free tiers** | interactive prototyping | free GPU credit is small and availability varies |
| **RunPod** (pay per second, ~$0.20–0.40/h for consumer GPUs) | a few hours on a big GPU, then stop | a pod is someone else's machine: zone `global`, Green-tier only. Never join it to your Tailscale as a `home` machine: the home rung would then count it as local |
| **E2E Networks / Yotta (India, INR, UPI)** | the same, in India, with Indian invoicing | E2E's published GPU rates run from ₹49/h (L4) up; confirm the region and terms for regulated data |

### Do not

| Option | Why not |
|---|---|
| **Vast.ai and other crowd-sourced hosts** for anything but public data | the host machine's owner can read what runs on it |
| **Lambda, Hyperstack, CoreWeave, TPU pods** | built for multi-GPU training clusters; nothing in SecuRAX needs that |
| **IndiaAI Compute Portal** (subsidised GPUs, about ₹65/GPU-hour in the official PIB note) | **Not eligible as an individual employee.** It is for DPIIT-recognised startups, academia, researchers and government. It becomes relevant only if SecuRAX ever becomes a registered startup. |
| **C-DAC AIRAWAT / PARAM** | for formal research proposals from eligible institutions |
| **Model splitting across devices** (RAMDeck / llama.cpp RPC) | see doc 56 |
| **Google TRC (free TPUs)** | for academic or open research by application; TPUs suit training, not this estate's inference |

## 3. Worst cases, and what protects you

| Worst case | Protection |
|---|---|
| A free tier changes its terms or limits overnight | the chains skip a dead rung and end in local; `./securax models` repairs model names |
| A paid rung runs up a bill | the router's monthly `max_budget`; paid rungs are opt-in only |
| Private data reaches a rented machine | residency (`./securax residency enable`) keeps Red-tier on zone `local`; `home` accepts only addresses you own; cloud GPUs are `global`; `e2e-in` is `global` until confirmed |
| A notebook session dies mid-job | use notebooks for restartable batch jobs only, with checkpoints written to your own storage |
| The laptop runs out of memory | `profile`/`autosize` size everything to what Docker sees; lite mode; 8-bit context cache |
