#!/usr/bin/env python3
"""Turn the red-team scorecard + AI-SPM posture into a board-ready risk narrative.

The JD asks for exactly this: "translate findings into board-ready risk narratives and
prioritised remediation roadmaps." This renders a one-page Markdown brief (which also
converts cleanly to the morning-brief style HTML or a PDF).

    python3 redteam/board_report.py --redteam redteam/results.json \
        --aispm docs/aispm-report.json --out docs/board-brief.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib

RATING = [(0.95, "LOW", "🟢"), (0.80, "MODERATE", "🟡"), (0.0, "HIGH", "🔴")]


def rating(score: float) -> tuple[str, str]:
    for threshold, label, icon in RATING:
        if score >= threshold:
            return label, icon
    return "HIGH", "🔴"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--redteam", required=True)
    ap.add_argument("--aispm", required=True)
    ap.add_argument("--out", default="docs/board-brief.md")
    args = ap.parse_args()

    rt = json.loads(pathlib.Path(args.redteam).read_text())
    sp = json.loads(pathlib.Path(args.aispm).read_text())
    today = dt.date.today().isoformat()

    overall = round((rt["defense_rate"] + sp["posture_score"]) / 2, 3)
    label, icon = rating(overall)

    gaps = [c for c in sp["controls"] if c["status"] == "GAP"]
    undef = [r for r in rt["results"] if not r["defended"]]

    lines = [
        f"# AI Security Assurance - Board Brief ({today})",
        "",
        f"## Residual risk: {icon} **{label}**  (composite assurance {overall:.0%})",
        "",
        "| Dimension | Score | Reading |",
        "|---|---|---|",
        f"| Adversarial-ML defence rate | {rt['defense_rate']:.0%} | "
        f"{rt['defended']}/{rt['total_attacks']} OWASP-LLM/ATLAS attacks defended |",
        f"| False-positive (business impact) | {rt['false_positives']}/{rt['benign_requests']} | "
        f"legitimate banking queries wrongly blocked |",
        f"| AI-SPM control coverage | {sp['posture_score']:.0%} | "
        f"{sp['controls_passed']}/{sp['controls_total']} baseline controls implemented |",
        "",
        "## What this estate is",
        "A multi-cloud AI cyber range (AWS + GCP + Azure + on-prem/laptop) with a single",
        "guardrail gateway enforcing input/output policy in front of every model, defended",
        "by Kubernetes admission control, zero-trust egress and runtime detection, all under",
        "a hard monthly cost ceiling.",
        "",
        "## Top risks & remediation roadmap (prioritised)",
    ]
    if not gaps and not undef:
        lines.append("- No open control gaps or undefended attack classes in the current baseline. "
                     "Focus shifts to **continuous assurance**: expand the red-team corpus (agentic "
                     "tool-abuse, multi-turn), add drift monitoring, and run the suite on every deploy.")
    else:
        for i, g in enumerate(gaps, 1):
            lines.append(f"- **P{i} [{g['control']} / {g['frameworks']}]** {g['description']} - *GAP, remediate*.")
        for r in undef:
            lines.append(f"- **[{r['id']}]** attack not fully defended "
                         f"(OWASP {r['owasp_llm']}, ATLAS {r['mitre_atlas']}) - tune rule / add detector.")

    lines += [
        "",
        "## Regulatory posture (India BFSI)",
        "- **DPDP Act 2023 / DPDP Rules 2025**: Aadhaar/PAN/card/UPI redacted at the gateway "
        "before any model call; audit log retained for breach reporting.",
        "- **RBI FREE-AI (Aug 2025) & cyber-resilience directions**: data residency in Mumbai regions, "
        "fail-closed guardrails, human-in-the-loop on high-impact actions, full decision audit.",
        "- **Frameworks evidenced**: NIST AI RMF, ISO/IEC 42001, CSA AI Controls Matrix, Google SAIF, "
        "OWASP LLM & Agentic Top 10, MITRE ATLAS (see docs/compliance-matrix.md).",
        "",
        "## Spend",
        "- Default posture runs on free tiers / credits; hard budget 2,500 INR/month with "
        "automated kill-switches on every cloud. Paid detectors are opt-in per drill.",
        "",
        "---",
        "_Generated from `redteam/results.json` and `docs/aispm-report.json`. "
        "Re-runs on every CI pipeline so the brief never goes stale._",
    ]
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}  (residual risk {label}, composite {overall:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
