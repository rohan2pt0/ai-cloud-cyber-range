# Model factory: judges, routers, monitors and open weights, done the tested way

**Owner, 2026-11-20.** The owner shared a set of published results from a post-training company (judges, decision graders, a
cost router, failure clustering, a research agent, secure open-weight deployment) and asked that every approach that adds real
value be built into the SecuRAX estate, with the settings that make it work. This spec keeps those settings, says where each
one lives in SecuRAX, and orders the work 80/20. Sources are cited by name and paraphrased, never copied.

**The one idea under all of it:** a cheap model does the first pass at scale, a calibrated threshold decides what a person or
a strong model looks at, and every decision is scored against the outcome that happened later. Quality and cost are scored
separately. The harness and the context are improved first; training a model comes last, only for the biggest workloads.

## 1. The techniques and their settings

### 1.1 A cheap monitor with a calibrated threshold

- **What:** after each step, a cheap model scores a sample of traces for cheating (reward hacking, faked passes). A score over
  the threshold wakes an investigator agent, which looks for the pattern across the whole run and alerts the owner. A confirmed
  hack rolls back to the last good checkpoint.
- **Settings that matter:**
  - The prompt is tuned for **partial AUROC under 10% false-positive rate**, not F1 or full AUROC. Above that rate, people
    stop reading the alerts.
  - The live threshold is set at **2% false positives**.
  - Score on **real past failures**, a few runs averaged, one sample per case.
- **Published result:** at 2% false positives, a cheap open model on low reasoning matched the recall of an expensive model
  for **under half the cost** per classification.

### 1.2 The decision grader: one call, a probability per criterion

- **What:** instead of one long judgement per rubric item, one call returns a yes/no probability for **every criterion at once**.
- **Published result:** on 100 tasks (407 criteria), about **32× cheaper**, **8× faster**, and **94% agreement** with the
  long-form judge.
- **The confidence band does the triage:**
  - When the grader is confident (above 70% or below 30%), it agrees **99%** of the time.
  - Between **30% and 70%**, the rubric item itself is usually ambiguous. Send it to a person, or rewrite the criterion.
    Never train or merge on it.

### 1.3 Decision models: a small head on a language model

- **What:** a language-model backbone plus a small learned **decision head** that outputs one score per answer choice,
  softmaxed into probabilities.
- **Training:** **Brier or cross-entropy** loss, updating both the head and the backbone.
- **Published result:** toxic-comment F1 rose from **0.48 to 0.68** on 50k training examples, in under an hour on four
  large GPUs.

### 1.4 Two stages: high recall first, high precision second

- **What:** the cheapest **well-calibrated** model (low Brier score and calibration error) runs with a **low threshold**, so it
  misses little. A second, more precise model checks only what the first pass flagged.
- **The rule:** choose the first-stage model for calibration, not accuracy.

### 1.5 Failure-mode clustering (a map-reduce taxonomy)

- **What:** sample traces, **cluster** them into candidate failure types, **assign and aggregate** every trace to a type, then
  **annotate**. Types nest, so the taxonomy is built recursively.
- **Why:** reading traces by hand misses rare failures at scale. The taxonomy shows the top failure types and how often each
  happens.

### 1.6 The router: cheap by default, strong when the signals say so

- **What:** a coding agent starts on a cheaper model and switches to the strong one only when a switch pays.
- **Escalation signals** (share of escalations in the published live traffic):
  - environment, permission or network error, 16%;
  - failing tests, 12%;
  - a script crash, 9%;
  - a git error, 6%;
  - a rejected patch, 3%;
  - the person approving a plan or giving new direction.
- **Hand-back signals:** routine steps such as waiting on a running command, a git step or a tool call.
- **Count the cost of switching:** a switch loses the prompt cache, so the router weighs quality, the cost of continuing and
  the cost of switching together.
- **Labels and scoring:**
  - Labels come from **terminal outcomes**, the whole turn judged with hindsight; isolated steps judged poorly.
  - Quality and cost are scored **separately**.
- **Published result:** **45% to 76%** of the strong-model cost at near-equal quality. A separate customer router cut costs up
  to **47%**.

### 1.7 A research agent with a notebook

- **What:** an agent with the same tools as the researchers. It curates data, edits code, launches runs, is **woken every k
  steps** by a monitor, and keeps a **persistent notebook** of what it has learned. It turns findings into reports with graphs.
- **How it was improved:** it was hill-climbed on past **decision points**, each graded against the fix the people later
  shipped.

### 1.8 A small model trained to use a precomputed index

- **What:** a 35B open model (about 3B active) was trained to search a **precomputed index** of about 9,000 repositories.
- **Published result:** about **100× cheaper** than a frontier model, at 2–10× lower latency. As the corpus grew from 20 to 300
  repositories, plain grep slowed **11×** and the index only **1.2×**.

### 1.9 Harness first, then post-training

- **The order:**
  - Improve the **context and the harness** first; most of the cheap gains are there.
  - Post-train only when that is exhausted, and first for the **largest, most expensive workloads**, where small gains
    compound, and for **custom tools** that general models do not know.
- **Post-training recipes, kept for later:**
  - **Specialists distilled into one model:** a short warm-up, then data split into partitions, one specialist per partition,
    then multi-teacher distillation. Two partitions gave 91% of the gain, and more different partitions beat random ones.
  - **Learning from production traces:** record the **exact tokens** the deployment produced, then train with score
    centering and a sampled KL penalty.
  - **Low precision:** 4-bit inference with quantization-aware distillation roughly halved the serving hardware.

### 1.10 Deploying open weights securely

From one published framework, aligned with NIST AI 600-1, the NSA-led joint guides on deploying AI systems securely and on AI
data security, and the Australian Signals Directorate-led guide on careful adoption of agentic AI.

- **Where it runs:** in infrastructure the enterprise controls, so the model's developer sees no inputs, outputs or usage.
- **An agent privilege contract:**
  - **What it may change:** history and backups kept outside the agent's reach, and approval needed for irreversible change.
  - **Where it may connect:** which hosts it may reach and what it may send, denied by default.
  - **Whose rights:** it acts within the invoking person's rights, and delegating to another agent never adds rights.
  - **Audit logs it cannot edit:** inputs, tool calls, state changes and outputs, kept where the agent cannot edit or delete them.
- **Evaluation before production:**
  - **Realistic data, no test cues:** production-like data, with names and cues that reveal a test removed. Models behave
    differently when they know they are tested.
  - **Ablations:** across model families and harness parts.
  - **A taxonomy of failures:** fitted to the deployment.
  - **Monitoring agents:** they read the traces.
- **Backdoors are possible, and evaluations cannot rule out a narrow, unknown trigger.** Guardrails and permissions therefore
  limit the damage of what an evaluation misses. The published evaluations disagree:
  - One security vendor saw a model's vulnerable-code rate rise from 19% to 27% under a political trigger.
  - Another found no affiliation effect across four models and six personas.

### 1.11 Model choice

- **Sensitive work:** prefer open weights with open training data and a clear licence. Examples are a fully open vision-language
  model with its datasets and recipes, a 501B mixture-of-experts model (23B active, 1M context) under Apache 2.0, Gemma and
  OLMo.
- **Any strong open model:** usable behind the rails once section 2.3's experiment has measured it.
- **Choose the quantization** to fit the hardware, and record it on the model card.

## 2. Where each one lives in SecuRAX, in value order

### Now: no GPU, cheap, saves tokens and catches bad builds

1. **A repository index for the builders (1.8).**
   - **What:** a precomputed symbol and section index of `ops.js`, `index.html` and the docs, which the delegated builders
     query instead of grepping and reading 10,000-line files.
   - **Measure:** tokens per build before and after.
   - **Why first:** the open-model plan's monthly cap went in one day on re-reading big files, and this attacks that directly.
2. **A decision-grader diff judge on every delegated build (1.2, 1.1).**
   - **What:** one call returns yes/no probabilities for the rules diffcheck cannot see: a test skipped or weakened, only a
     lesson line changed, a gate edited, the brief not met.
   - **Calibration:** on our own past builds (the empty "green" builds and the weakened-test cases are the labelled hacks),
     at about 2% false positives.
   - **The 30–70% band:** goes to the reviewer with the criterion named.
   - **Where:** it extends `lifecycle/diffcheck.py` and `lifecycle/review.py` (one call per PR).
3. **The router in the delegation loop (1.6).**
   - **What:** start each brief on the cheapest working open model. Escalate on the published signals, which the loop can
     already see:
     - failing tests;
     - environment or permission errors;
     - a script crash;
     - a git error;
     - a rejected review.
   - **Hand back** after routine steps.
   - **Score:** quality (did it merge green) and cost (tokens) separately, from git and CI.
   - **Where:** `lifecycle/delegate_here.sh` and `lifecycle/route.py`; the second provider (OpenRouter) is already authorised.
4. **Failure clustering of build logs (1.5).**
   - **What:** a map-reduce taxonomy over autobuild and delegation logs and over CI failures. Its top types write the
     LESSONS lines and the brief warnings, by count.
   - **Where:** it replaces the hand-written lesson for repeat failures.

### Next: the gateway and the range

5. **The agent privilege contract (1.10).** One contract, with a test for each line. It maps onto what exists:
   - the gateway rails, identity and residency;
   - the kill switch;
   - the tamper-evident audit chain, moved out of any agent's reach;
   - permissions in `governance/identity.json`.
6. **Two-stage triage at the gateway (1.4).**
   - **What:** a cheap, calibrated first pass for prompt injection and data leaving; a precise second model for what it flags.
   - **Where it extends:** the SOC alert items in the queue (`soc-control-alerts`, `soc-auth-refusal-alerts`).
7. **A trace monitor on the gateway (1.1).**
   - **What:** a sampled judge over the audit chain for unexpected agent actions, at a 2% false-positive threshold. Its alerts
     go to the owner's phone push.
8. **The range experiment (1.10).**
   - **What:** the same coding task across models, with and without trigger personas (a bank, a region, industrial control),
     with no test cues. The existing scanners measure the vulnerable-code rate.
   - **Also:** a trigger probe in the red-team journeys (MITRE ATLAS).
   - **It is a paper:** `ip-first` applies.

### Later: rails only, until a GPU and a measured need exist

9. **A research-agent loop (1.7):**
   - **What:** the navigator's queue and LESSONS act as its persistent notebook, scheduled check-ins wake it, and its decisions
     are graded against the fix that later merged.
10. **Decision models (1.3):** a small classifier for the Life OS message reader and alert triage, trained only when labelled
    data exists. Until then, the rail is the model registry and the eval set.
11. **Post-training (1.9):** specialist distillation, learning from production traces (opt-in, private, exact tokens) and
    low-precision serving. Each is declared in `governance/evolution.json` as a growth path, not built.

## 3. Rules that hold all of it

- **Calibrate on our own labelled failures**, never on a public benchmark alone. Report recall at the chosen false-positive
  rate.
- **Measure quality and cost separately**, and keep both numbers per change, in `progress`.
- **Harness and context first.** A model is trained only when the harness is exhausted and the workload is the biggest.
- **Sensitive data stays local.** Any model sits behind the gateway rails, and no evaluation result ever loosens a permission.
- **Every slice ships with a test, and with its threat model when it crosses a trust boundary.**

## 4. Not tested yet

None of this is built. The numbers above are the publisher's, on their workloads. Each slice must reproduce its own number on
ours before it is trusted.
