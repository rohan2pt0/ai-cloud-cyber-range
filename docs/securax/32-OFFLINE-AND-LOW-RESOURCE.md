# 32 · Powerful offline, sharp on a small machine — what we took from the most-starred repos, and what we measured

<!-- status:start (from docs/status.yml; edit that file, then run docs/sync_status.py) -->
> **Status: 🟢 Built.** `offline_power` journey. [What the lights mean](../index.md#the-status-lights)
<!-- status:end -->

**How the repos were chosen.** Candidates were named from the problem (run offline, run small, security data that does not need the internet), then each repo's **public page was fetched** for stars and licence (numbers below are as shown on those pages on 2026-10-14; the pages did not show last-commit dates). Blog "top 10" lists were *not* used for ratings: they disagreed with each other.

| Repo | Stars | Licence | Verdict |
|---|---|---|---|
| ggml-org/**llama.cpp** | 131.1k | MIT | **Already underneath us** (Ollama runs it). Plain C/C++, no dependencies, 1.5–8-bit quantisation, AVX/AVX2/AVX512. Nothing to add directly. |
| mitre-attack/**attack-stix-data** | 699 | MITRE ATT&CK Terms of Use | ✅ **Adopted** as an offline snapshot (slim). Stars understate its role: it *is* the canonical dataset. |
| CISA KEV (cisa.gov feed; mirror cisagov/**kev-data**) | mirror 127 | CC0 | ✅ **Adopted** as an offline snapshot. |
| microsoft/**BitNet** | 41.1k | MIT | ⏸ **Not adopted: measure first.** The project claims 2.37–6.17× CPU speed-up and 72–82 % less energy on x86 with 1.58-bit models; those are *its* numbers, and the only official chat model listed is a 2B one. Needs a build toolchain. `./securax bench` is how you would find out whether it beats a quantised 3–4B on your machine. |
| ggml-org/**whisper.cpp** | 54.4k | MIT | ⏸ Candidate for **offline dictation** (CPU-only; tiny 75 MiB … large 2.9 GiB unquantised). Not built. |
| Mozilla-Ocho/**llamafile** | 26.2k | Apache-2.0 | ⏸ Candidate **zero-install fallback binary**. Ollama already covers the need. Not built. |
| redcanaryco/**atomic-red-team** | 12.7k | MIT | ⏸ **Backlog** for the AD range / purple loop (1,878 atomics run on *endpoints*, not our gateway). Not built. |
| SigmaHQ/**sigma** | 11.2k | Detection Rule License 1.1 | ⏸ **Backlog**: 3,000+ rules for *log sources*; our SOC reads gateway/Falco events. It pays off when the Wazuh organ is running. Attribution required. |
| google/**osv-scanner** | 11.2k | Apache-2.0 | ⏸ Supports fully offline scans against a downloaded DB. We already scan with Trivy; not duplicated. |
| asg017/**sqlite-vec** | 8.2k | Apache-2.0 / MIT | ❌ **No**: pre-v1 ("expect breaking changes"); AnythingLLM already bundles a local vector DB. |

## What was built
**1 · Offline threat intel** — `./securax offline sync | status`, `./securax kev CVE-…`
* Two snapshots in `~/.securax/intel`: CISA **KEV** (1,741 known-exploited CVEs) and MITRE **ATT&CK** Enterprise (706 techniques → name + tactics).
* **Built for small machines:** the 55 MB MITRE bundle is *streamed* object-by-object: measured **2.5 s and 54 MB peak memory**, keeping **53 KB** (KEV 348 KB). Downloads are size-capped and written atomically.
* **Failure-tolerant:** a failed or oversized refresh **never destroys a good snapshot**; a dead first URL falls back to a mirror; a file that is not what we expect is refused.
* **Used by:** the AI-SOC (incidents now carry technique names, e.g. `T1190` → *Exploit Public-Facing Application*, with **no network**) and `./securax scan` (after Trivy, flags which CVEs are **known-exploited right now**, and notes how stale the snapshot is).
* Verified with the network deliberately **dead**: lookups and enrichment still answer; `sync` fails safe.

**2 · `./securax bench`** — which of *your* installed models should *this* machine use?
* Measures each installed Ollama model (nothing is downloaded): **fits RAM** (size × 1.25 vs RAM minus a 4 GB reserve), **accuracy** on 8 deterministic security tasks (injection triage, secret spotting, MITRE id, IOC extraction, India's DPDP Act, incident next step, JSON discipline), **tokens/second**, time to answer.
* Recommends the best model that fits, is accurate enough (≥ 60 %) and fast enough (≥ 4 tok/s); `--apply` writes `LOCAL_MODEL`. On a machine where nothing qualifies it **says so** instead of recommending something that would swap.
* Why: [the guides](https://www.popularai.org/p/best-cpu-only-local-llm-2026) rank generic models and expect only 5–15 tokens/s from 3–7B models on a 16 GB CPU; none knows your hardware. This replaces guessing with a one-minute measurement.

## Honest limits
* Star counts are a popularity signal, not a quality one; the licence and the fit to our architecture decided each verdict.
* **`bench` is a smoke test** of 8 short tasks: it rules models out and compares them *on this machine*; it is not a leaderboard and says nothing about long-context or coding quality. The thresholds (60 %, 4 tok/s, 1.25× RAM) are judgement calls, adjustable by flags.
* I could **not** run a real model benchmark here (no GPU/CPU-model install in this sandbox): the harness is proven against a fake Ollama (mechanics, scoring, recommendation logic). **Your first real run is the first real measurement.**
* KEV is only as fresh as your last sync (the tools say how old it is). ATT&CK/KEV are public data; `scan` still needs the internet **once** for Trivy's own database.
* Not built: BitNet, whisper.cpp dictation, llamafile, Sigma/Atomic content (see table).
