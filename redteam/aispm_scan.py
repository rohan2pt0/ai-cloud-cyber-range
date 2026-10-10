#!/usr/bin/env python3
"""Mini AI-SPM (AI Security Posture Management) scanner.

Walks the repo and produces an inventory of AI assets + a posture scorecard against a
control baseline distilled from NIST AI RMF, ISO/IEC 42001, CSA AI Controls Matrix and
Google SAIF. This is the "AI-BOM + posture" artefact an AI-SPM tool (Wiz, Prisma AIRS,
Microsoft Defender for AI) would produce - built from first principles so you can speak
to how it works, not just which product to buy.

    python3 redteam/aispm_scan.py --root . --out docs/aispm-report.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

CONTROLS = [
    # (id, framework refs, description, detector returns (passed, evidence))
    ("AISPM-01", "SAIF/LLM01", "Input guardrails (prompt-injection) present"),
    ("AISPM-02", "ISO42001/LLM02", "PII redaction for India BFSI identifiers"),
    ("AISPM-03", "NIST-AI-RMF-MANAGE/LLM05", "Output guardrails (exfil/secret) present"),
    ("AISPM-04", "SAIF/LLM07", "System-prompt canary leak detection"),
    ("AISPM-05", "CSA-AICM/LLM10", "Resource limits / rate limiting"),
    ("AISPM-06", "SAIF", "Models have no direct internet (egress NetworkPolicy)"),
    ("AISPM-07", "ISO42001", "Admission control hardening (Kyverno)"),
    ("AISPM-08", "NIST-AI-RMF", "Cost budget / kill-switch per cloud"),
    ("AISPM-09", "CSA-AICM", "Audit logging of all AI decisions"),
    ("AISPM-10", "SAIF", "Red-team suite in CI (adversarial ML)"),
]


def read_all(root: pathlib.Path) -> str:
    blob = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".yaml", ".yml", ".tf", ".sh", ".md"} and ".git" not in p.parts:
            try:
                blob.append(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:  # noqa: BLE001
                pass
    return "\n".join(blob)


def inventory(root: pathlib.Path) -> dict:
    corpus = read_all(root)
    models = sorted(set(re.findall(r"(?:ollama/|gemini/|bedrock/|azure/)[\w.\-:/]+", corpus)))
    detectors = sorted(set(re.findall(r"(llama-guard|model-armor|prompt-shields|bedrock-guardrail)", corpus)))
    clouds = [c for c in ("aws", "google", "azurerm") if re.search(rf'provider "{c}"', corpus)]
    return {"models": models, "guardrail_detectors": detectors, "cloud_providers": clouds}


def posture(root: pathlib.Path) -> list[dict]:
    corpus = read_all(root)

    def has(*pats: str) -> tuple[bool, str]:
        for pat in pats:
            if re.search(pat, corpus, re.I):
                return True, pat
        return False, ""

    checks = {
        "AISPM-01": has(r"detect_prompt_injection"),
        "AISPM-02": has(r"redact_pii", r"AADHAAR"),
        "AISPM-03": has(r"check_output", r"OUT-md-image-exfil"),
        "AISPM-04": has(r"canary", r"LEAK-system-prompt-canary"),
        "AISPM-05": has(r"enforce_limits", r"RATE_LIMIT_PER_MIN"),
        "AISPM-06": has(r"default-deny-all", r"NetworkPolicy"),
        "AISPM-07": has(r"kind:\s*ClusterPolicy", r"kyverno"),
        "AISPM-08": has(r"budgets_budget", r"billing_budget", r"consumption_budget"),
        "AISPM-09": has(r'logging\.getLogger\("audit"\)', r"audit-log-path"),
        "AISPM-10": has(r"run_attacks", r"promptfoo"),
    }
    out = []
    for cid, fw, desc in CONTROLS:
        passed, evidence = checks[cid]
        out.append({"control": cid, "frameworks": fw, "description": desc,
                    "status": "PASS" if passed else "GAP", "evidence": evidence})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()

    controls = posture(root)
    passed = sum(c["status"] == "PASS" for c in controls)
    report = {
        "inventory": inventory(root),
        "posture_score": round(passed / len(controls), 3),
        "controls_passed": passed,
        "controls_total": len(controls),
        "controls": controls,
    }
    print(json.dumps(report, indent=2))
    if args.out:
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.out).write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
