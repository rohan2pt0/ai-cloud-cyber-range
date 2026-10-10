# Personal R&D Lab (OPSEC · OSINT · LifeOS · Financial Freedom)

A **defensive, self-scoped** sandbox that rides on the same AI-security plumbing as the
cyber range. The theme: treat *yourself* as the asset — your identity, your data, your
money, your time — and apply the same rigour (threat-model, measure, reduce) you apply to
client AI systems. Everything here runs on the laptop for free and reuses the guardrail
engine, so it doubles as real privacy-engineering practice (indirect
prompt-injection defence, secure automation).

> Ethics & scope: these tools operate on **your own** identifiers and accounts only. They
> are for personal defence and hygiene — not for profiling, tracking, or deanonymising
> other people. Keep it that way.

## 1. OPSEC — `self_opsec.py`
- **Password exposure** via HIBP k-anonymity range API (only a 5-char hash prefix leaves
  the machine; your password never does).
- **Digital-footprint review** — paste your own bio/resume/profile; it flags Aadhaar/PAN/
  card/mobile/email you're over-sharing (DPDP lens) *and* detects hidden prompt-injection
  in scraped profile text before any LLM summarises it.
- **OPSEC posture score** — a 10-point checklist (unique passwords, MFA/passkeys, SIM-swap
  lock, disk encryption, 3-2-1 backups, billing alerts…) scored like the range's AI-SPM.

```bash
python3 personal-rnd/self_opsec.py --footprint-file my_public_bio.txt
python3 personal-rnd/self_opsec.py --check-password --online
python3 personal-rnd/self_opsec.py --opsec my_opsec_answers.json
```

## 2. OSINT (self-reconnaissance)
Run searches on your **own** name/handles/email to see your exposed surface, then feed the
collected text through `footprint_review()` so it's sanitised and PII-tagged before you
summarise it with an LLM. Manual, periodic, you-only. The point is reduction: close old
accounts, scrub PII, split identities.

## 3. LifeOS — `lifeos.py`
A tiny planning layer over the connectors you already have (Notion, Todoist, Google
Calendar, Gmail). It does not store anything itself; it helps you structure goals →
projects → next-actions and keeps a weekly-review template. Treat your LifeOS data with
the same classification discipline as work data (that's the security angle).

## 4. Financial freedom — `fin_freedom.py`
A FIRE (Financial Independence) calculator for Indian context: corpus target from the
4%/3.5% safe-withdrawal rule, years-to-FI from savings rate, and an emergency-fund check.
Read-only and offline — it does maths on numbers you type. For live portfolio data use the
INDMoney connector in the app; never hard-code account numbers here (and if you paste any,
`self_opsec.py` will flag them).

## Why this belongs in the range
- **Privacy-by-design & DPDP** — the exact skill four JDs ask for, applied to real data.
- **Indirect prompt-injection** — OSINT text is attacker-controlled; sanitising it is OWASP
  LLM01/ASI01 in practice.
- **Secure automation** — connector use with least privilege and audit is the agentic-SecOps
  muscle (ASI02/ASI03) on your own life, where the blast radius is yours to own.
