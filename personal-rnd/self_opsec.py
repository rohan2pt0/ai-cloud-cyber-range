"""Personal OPSEC / self-OSINT toolkit — DEFENSIVE, SELF-SCOPED ONLY.

Treats *you* as the asset to defend ("personal attack-surface management"). It helps you
see what an attacker could learn about you and reduce it. It deliberately does NOT target,
profile, or deanonymise other people — every function takes your own identifiers.

Doubles as range practice: OSINT findings are often attacker-controlled text, so we pass
them through the same guardrail engine the gateway uses before they ever reach an LLM
summariser (indirect prompt-injection defence, OWASP LLM01/ASI01).

Networked checks use privacy-preserving patterns:
  * password exposure via HIBP **k-anonymity range API** (only a 5-char SHA1 prefix leaves
    your machine; the full hash / password never does).
Offline by default; pass --online to enable the range check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "apps" / "llm-gateway"))
from app import guardrails  # noqa: E402


# --------------------------------------------------------------------------- #
# 1. Password exposure (k-anonymity: full secret never leaves the machine)
# --------------------------------------------------------------------------- #
def password_pwned_count(password: str, online: bool) -> int | None:
    """Return breach count for YOUR password via HIBP range API, or None if offline.

    Only the first 5 hex chars of the SHA-1 are sent; the API returns a list of suffixes
    and we match locally. This is the industry-standard privacy-preserving check.
    """
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    if not online:
        return None
    import httpx
    r = httpx.get(f"https://api.pwnedpasswords.com/range/{prefix}",
                  headers={"Add-Padding": "true"}, timeout=10)
    r.raise_for_status()
    for line in r.text.splitlines():
        suf, _, count = line.partition(":")
        if suf == suffix:
            return int(count)
    return 0


# --------------------------------------------------------------------------- #
# 2. Digital-footprint self-review: scan text YOU paste (e.g. your own bio,
#    resume, a public profile) for identifiers you may be over-sharing.
# --------------------------------------------------------------------------- #
def footprint_review(text: str) -> dict:
    """Flag PII you're exposing about yourself, reusing the gateway's DPDP detectors."""
    _, findings = guardrails.redact_pii(text)
    exposed: dict[str, int] = {}
    for f in findings:
        label = f.rule.replace("PII-", "")
        exposed[label] = exposed.get(label, 0) + 1
    # Injection check: if this text came from a web profile, it may carry hidden instructions.
    inj = guardrails.detect_prompt_injection(text)
    return {
        "identifiers_exposed": exposed,
        "total_exposed": sum(exposed.values()),
        "embedded_injection_risk": [f.rule for f in inj],
        "advice": _advice(exposed),
    }


def _advice(exposed: dict) -> list[str]:
    tips = []
    if "AADHAAR" in exposed:
        tips.append("Aadhaar found: never post it; use masked/VID. DPDP + UIDAI violation risk.")
    if "CARD_PAN" in exposed:
        tips.append("Card number found: remove immediately (PCI DSS).")
    if "IN_MOBILE" in exposed or "EMAIL" in exposed:
        tips.append("Contact details exposed: consider an alias email + a separate number for public profiles.")
    if "INCOME_TAX_PAN" in exposed:
        tips.append("PAN found: high-value for impersonation/loan fraud; redact from public docs.")
    if not exposed:
        tips.append("No high-risk identifiers detected in this sample. Good footprint hygiene.")
    return tips


# --------------------------------------------------------------------------- #
# 3. OPSEC posture self-checklist (scored)
# --------------------------------------------------------------------------- #
OPSEC_CHECKS = [
    ("unique_passwords", "Every account has a unique password (manager-generated)"),
    ("mfa_everywhere", "MFA/passkeys on email, bank, cloud, GitHub, brokerage"),
    ("hardware_key", "Hardware security key (FIDO2) for the crown-jewel accounts"),
    ("separate_identities", "Work / personal / public identities separated (email + browser profiles)"),
    ("disk_encryption", "Full-disk encryption on the Spectre (BitLocker) + strong boot PIN"),
    ("breach_monitoring", "Breach monitoring on all your emails (HIBP notify)"),
    ("minimal_public_pii", "No Aadhaar/PAN/DOB/address on any public profile"),
    ("sim_lock", "SIM PIN + carrier port-out lock (SIM-swap defence)"),
    ("backup_321", "3-2-1 backups, at least one offline/immutable"),
    ("cloud_budget_alerts", "Billing alerts on every personal cloud account"),
]


def opsec_score(answers: dict[str, bool]) -> dict:
    passed = [k for k, _ in OPSEC_CHECKS if answers.get(k)]
    gaps = [{"id": k, "action": d} for k, d in OPSEC_CHECKS if not answers.get(k)]
    return {"score": round(len(passed) / len(OPSEC_CHECKS), 2),
            "passed": len(passed), "total": len(OPSEC_CHECKS), "gaps": gaps}


def main() -> int:
    ap = argparse.ArgumentParser(description="Personal OPSEC / self-OSINT (defensive).")
    ap.add_argument("--footprint-file", help="A text file about YOU to review for over-sharing.")
    ap.add_argument("--check-password", action="store_true", help="k-anonymity breach check for a password you type.")
    ap.add_argument("--opsec", help="JSON file of {check_id: true/false} for the posture score.")
    ap.add_argument("--online", action="store_true", help="Allow the HIBP range API call.")
    args = ap.parse_args()

    out: dict = {}
    if args.footprint_file:
        text = pathlib.Path(args.footprint_file).read_text(encoding="utf-8", errors="ignore")
        out["footprint"] = footprint_review(text)
    if args.check_password:
        import getpass
        n = password_pwned_count(getpass.getpass("Your password (never stored/sent): "), args.online)
        out["password"] = ("offline — rerun with --online" if n is None
                           else f"seen in {n} breaches — CHANGE IT" if n else "not found in known breaches")
    if args.opsec:
        out["opsec"] = opsec_score(json.loads(pathlib.Path(args.opsec).read_text()))
    if not out:
        out = {"opsec_template": {k: False for k, _ in OPSEC_CHECKS},
               "hint": "Fill the template to a JSON file and pass --opsec file.json"}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
