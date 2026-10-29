"""Deterministic, dependency-free guardrails for the LLM gateway.

These are the *first* layer of a defence-in-depth chain. They are fast, explainable
and auditable (each verdict lists the rule that fired), which is what a regulator or
internal audit wants to see. Model-based detectors (Llama Guard, Model Armor,
Bedrock Guardrails, Azure Content Safety) are chained after these in providers.py.

Framework mapping (see docs/compliance-matrix.md):
  OWASP LLM01 / ASI01  -> detect_prompt_injection
  OWASP LLM02 / DPDP   -> redact_pii (India-specific identifiers)
  OWASP LLM05          -> check_output (exfil links, active content)
  OWASP LLM07          -> check_output (system prompt / secret leakage)
  OWASP LLM10          -> enforce_limits
  MITRE ATLAS          -> AML.T0051 (prompt injection), AML.T0054 (jailbreak),
                          AML.T0057 (LLM data leakage)
"""
from __future__ import annotations

import base64
import fnmatch
import json
import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class Finding:
    rule: str
    category: str  # owasp-llm / atlas id
    severity: str  # low | medium | high | critical
    detail: str = ""


@dataclass
class Verdict:
    allowed: bool
    findings: list[Finding] = field(default_factory=list)
    text: str = ""  # possibly transformed (redacted / sanitised) text

    @property
    def risk(self) -> str:
        order = ["none", "low", "medium", "high", "critical"]
        worst = max((order.index(f.severity) for f in self.findings), default=0)
        return order[worst]


# --------------------------------------------------------------------------- #
# Prompt injection / jailbreak heuristics
# --------------------------------------------------------------------------- #
_INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    # (rule id, regex, severity)
    ("PI-001-override", r"\b(ignore|disregard|forget|override)\b.{0,40}\b(previous|prior|above|earlier|all|your)\b.{0,30}\b(instructions?|rules|guidelines|guidance|directions|prompts?|directives|constraints|safeguards|polic(?:y|ies))\b", "high"),
    ("PI-002-sysprompt-exfil", r"\b(reveal|print|show|repeat|output|leak|tell me)\b.{0,40}\b(system|hidden|initial|developer)\s+(prompt|message|instructions?)\b", "high"),
    ("PI-003-roleplay-jailbreak", r"\b(DAN|do anything now|developer mode|jailbreak|unfiltered mode|no restrictions|god mode)\b", "high"),
    ("PI-004-new-identity", r"\byou are (now|no longer)\b|\bfrom now on,? you\b|\bact as (an? )?(unrestricted|evil|root|admin)", "medium"),
    ("PI-005-fake-delimiter", r"(</?(system|assistant|im_start|im_end)>|\[/?INST\]|<<SYS>>|###\s*(system|instruction))", "high"),
    ("PI-006-tool-coercion", r"\b(call|invoke|execute|run|use)\b.{0,20}\b(tool|function)\b.{0,40}\b(transfer|delete|send|export|exec|shell)\b", "high"),
    ("PI-007-hidden-instruction", r"\b(AI|assistant|agent|LLM|model)\s*(:|,)?\s*(please\s+)?(ignore|you must|new instructions?|important instructions?)\b", "medium"),
    ("PI-008-exfil-request", r"\b(send|post|upload|forward|exfiltrate)\b.{0,40}\b(to|at)\b.{0,10}(https?://|\w+@\w+\.\w+)", "high"),
]
_COMPILED_INJECTION = [(r, re.compile(p, re.I | re.S), s) for r, p, s in _INJECTION_PATTERNS]

# Unicode "tag" block (U+E0000..U+E007F) is used for ASCII smuggling: invisible to
# humans, readable by tokenisers. Also zero-width + bidi override characters.
_INVISIBLE = re.compile("[\U000E0000-\U000E007F​-‏‪-‮⁠-⁤﻿]")
_B64_BLOB = re.compile(r"\b[A-Za-z0-9+/]{40,}={0,2}")


def _decode_smuggled(text: str) -> str:
    """Return the hidden ASCII carried in Unicode tag characters (if any)."""
    return "".join(chr(ord(c) - 0xE0000) for c in text if 0xE0000 <= ord(c) <= 0xE007F)


def normalise(text: str) -> str:
    """Canonicalise text so trivial obfuscation does not bypass regexes."""
    text = unicodedata.normalize("NFKC", text)
    return _INVISIBLE.sub("", text)


def detect_prompt_injection(text: str) -> list[Finding]:
    findings: list[Finding] = []
    smuggled = _decode_smuggled(text)
    if smuggled:
        findings.append(Finding("PI-100-ascii-smuggling", "LLM01/AML.T0051", "critical",
                                f"hidden tag-characters decode to: {smuggled[:80]!r}"))
    if _INVISIBLE.search(text) and not smuggled:
        findings.append(Finding("PI-101-invisible-chars", "LLM01/AML.T0051", "medium",
                                "zero-width or bidi-override characters present"))

    candidates = [normalise(text)]
    if smuggled:
        candidates.append(smuggled)
    for blob in _B64_BLOB.findall(text):
        try:
            decoded = base64.b64decode(blob, validate=True).decode("utf-8", "ignore")
            if decoded.isprintable() and len(decoded) > 10:
                candidates.append(decoded)
        except Exception:  # noqa: BLE001 - not base64, ignore
            continue

    seen: set[str] = set()
    for cand in candidates:
        for rule, rx, sev in _COMPILED_INJECTION:
            if rule not in seen and rx.search(cand):
                seen.add(rule)
                cat = "LLM01/AML.T0054" if "jailbreak" in rule else "LLM01/AML.T0051"
                via = "" if cand is candidates[0] else " (in decoded payload)"
                findings.append(Finding(rule, cat, sev, f"matched pattern{via}"))
    return findings


# --------------------------------------------------------------------------- #
# PII detection & redaction - India BFSI identifiers (DPDP Act 2023, RBI, PCI DSS)
# --------------------------------------------------------------------------- #
_VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def verhoeff_valid(number: str) -> bool:
    c = 0
    for i, digit in enumerate(reversed(number)):
        c = _VERHOEFF_D[c][_VERHOEFF_P[i % 8][int(digit)]]
    return c == 0


def luhn_valid(number: str) -> bool:
    total = 0
    for i, d in enumerate(reversed(number)):
        n = int(d)
        if i % 2:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


_PII_RULES: list[tuple[str, re.Pattern[str], str, object]] = [
    # (label, regex, severity, validator or None)
    ("AADHAAR", re.compile(r"\b[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}\b"), "critical",
     lambda m: verhoeff_valid(re.sub(r"\D", "", m))),
    ("CARD_PAN", re.compile(r"\b(?:\d[ -]?){13,19}\b"), "critical",
     lambda m: luhn_valid(re.sub(r"\D", "", m)) and 13 <= len(re.sub(r"\D", "", m)) <= 19),
    ("INCOME_TAX_PAN", re.compile(r"\b[A-Z]{3}[PCHFATBLJG][A-Z]\d{4}[A-Z]\b"), "high", None),
    ("IFSC", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"), "low", None),
    ("UPI_ID", re.compile(r"\b[\w.\-]{2,256}@(?:ok)?(?:sbi|hdfcbank|icici|axisbank|ybl|paytm|upi|apl|ibl|axl)\b", re.I), "medium", None),
    ("IN_MOBILE", re.compile(r"(?<!\d)(?:\+91[ -]?|0)?[6-9]\d{9}(?!\d)"), "medium", None),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "medium", None),
]


def redact_pii(text: str) -> tuple[str, list[Finding]]:
    findings: list[Finding] = []
    out = text
    for label, rx, sev, validator in _PII_RULES:
        def _sub(m: re.Match[str], label=label, sev=sev, validator=validator) -> str:
            if validator and not validator(m.group(0)):  # type: ignore[operator]
                return m.group(0)
            findings.append(Finding(f"PII-{label}", "LLM02/DPDP", sev, "redacted"))
            return f"[{label}_REDACTED]"
        out = rx.sub(_sub, out)
    return out, findings


# --------------------------------------------------------------------------- #
# Output handling - LLM05 / LLM07
# --------------------------------------------------------------------------- #
_SECRET_PATTERNS = [
    ("SECRET-aws-akid", re.compile(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("SECRET-gcp-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("SECRET-private-key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("SECRET-github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("SECRET-jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
]
def _host(url: str) -> str:
    """Hostname of a URL found in model output. A URL the parser refuses (e.g. 'http://[abc') must not crash the output rails:
    it is attacker-influenced text, so a malformed URL is treated as an UNTRUSTED host (and removed), never as 'no host'."""
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return "invalid-url"


_MD_IMAGE = re.compile(r"!\[[^\]]*\]\((\S+?)\)")
_URL = re.compile(r"https?://[^\s)\"'>]+")
_ACTIVE = re.compile(r"<\s*(script|iframe|object|embed|img[^>]+onerror)|javascript:", re.I)


def check_output(text: str, allowed_domains: set[str], canaries: set[str] | None = None) -> tuple[str, list[Finding]]:
    findings: list[Finding] = []
    out = text

    for rule, rx in _SECRET_PATTERNS:
        if rx.search(out):
            findings.append(Finding(rule, "LLM02/AML.T0057", "critical", "credential in model output"))
            out = rx.sub("[SECRET_REDACTED]", out)

    for canary in canaries or set():
        if canary and canary in out:
            findings.append(Finding("LEAK-system-prompt-canary", "LLM07/AML.T0056", "critical",
                                    "system prompt canary token echoed"))
            out = out.replace(canary, "[CANARY]")

    # Markdown image rendering = zero-click exfiltration channel (EchoLeak class).
    def _img(m: re.Match[str]) -> str:
        host = _host(m.group(1))
        if host and not any(host == d or host.endswith("." + d) for d in allowed_domains):
            findings.append(Finding("OUT-md-image-exfil", "LLM05/ASI01", "high", f"image to {host}"))
            return "[external image removed]"
        return m.group(0)
    out = _MD_IMAGE.sub(_img, out)

    for url in _URL.findall(out):
        host = _host(url)
        if host and not any(host == d or host.endswith("." + d) for d in allowed_domains):
            findings.append(Finding("OUT-untrusted-link", "LLM05", "medium", host))
            out = out.replace(url, "[link removed]")

    if _ACTIVE.search(out):
        findings.append(Finding("OUT-active-content", "LLM05", "high", "script/iframe/js URI"))
        out = _ACTIVE.sub("[blocked]", out)
    return out, findings


# --------------------------------------------------------------------------- #
# Resource limits - LLM10 Unbounded Consumption
# --------------------------------------------------------------------------- #
def enforce_limits(text: str, max_chars: int) -> list[Finding]:
    if len(text) > max_chars:
        return [Finding("DOS-oversize-prompt", "LLM10", "medium", f"{len(text)} > {max_chars} chars")]
    return []


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
BLOCKING = {"high", "critical"}


def inspect_input(text: str, max_chars: int = 8000, redact: bool = True) -> Verdict:
    findings = enforce_limits(text, max_chars) + detect_prompt_injection(text)
    clean = normalise(text)
    if redact:
        clean, pii = redact_pii(clean)
        findings += pii
    blocked = any(f.severity in BLOCKING and not f.rule.startswith("PII-") for f in findings)
    blocked = blocked or any(f.rule == "DOS-oversize-prompt" for f in findings)
    return Verdict(allowed=not blocked, findings=findings, text=clean)


# Context the operator or the chat app puts in the system message: instructions, and often retrieved documents (RAG). Long by
# nature, so no size cap; and phrases such as "### Instruction" or "you are now" are normal there, so a match is recorded
# (audited, counted) but does not block. What is never legitimate in any context still blocks: hidden tag characters, and an
# order to send data to an address.
CONTEXT_BLOCKING = {"PI-100-ascii-smuggling", "PI-008-exfil-request"}


def inspect_context(text: str, redact: bool = True) -> Verdict:
    findings = []
    for f in detect_prompt_injection(text):
        if f.rule not in CONTEXT_BLOCKING and f.severity in BLOCKING:
            f = Finding(f.rule, f.category, "medium", f.detail + " (in the system context: recorded, not blocked)")
        findings.append(f)
    clean = normalise(text)
    if redact:
        clean, pii = redact_pii(clean)
        findings += pii
    blocked = any(f.severity in BLOCKING and not f.rule.startswith("PII-") for f in findings)
    return Verdict(allowed=not blocked, findings=findings, text=clean)


# --------------------------------------------------------------------------- #
# Agent actions - tool calls the MODEL asks for (OWASP LLM06 Excessive Agency / ASI02 Tool Misuse)
# --------------------------------------------------------------------------- #
# Tool RESULTS are already scanned as input (indirect injection). This checks the other direction: which tool the model wants
# to run and with what arguments, before the agent framework executes it.
DEFAULT_TOOL_POLICY: dict = {
    "allow": [],                                    # non-empty = ONLY these tools may be called (glob patterns)
    "deny": ["shell", "bash", "exec*", "run_command", "*delete*", "drop_*", "rm", "eval*"],
    "require_approval": ["*transfer*", "*payment*", "*send_money*", "wire_*", "send_email", "*refund*"],
}
_DESTRUCTIVE = re.compile(r"\brm\s+-[a-z]*r[a-z]*f|\bDROP\s+(TABLE|DATABASE|SCHEMA)\b|\bTRUNCATE\s+TABLE\b|\bmkfs\b|"
                          r"\b(curl|wget)\b[^|\n]*\|\s*(ba|z)?sh\b|\bchmod\s+-?R?\s*777\b|\bshutdown\s+-[hr]\b|:\(\)\s*\{", re.I)


def _match(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, p.lower()) for p in patterns or [])


def inspect_tool_calls(tool_calls: list[dict], policy: dict | None = None, canaries: set[str] | None = None,
                       approver=None) -> tuple[list[dict], list[Finding]]:
    """Check every tool call a model returned. Denied, unlisted or approval-requiring tools and destructive arguments are
    BLOCKING findings; personal data in arguments is redacted in place (data leaving through a tool is still data leaving).

    `approver` (optional, app.approvals) turns the approval-required block into an approve-then-proceed loop: a call whose
    exact (tool, args) a human has granted is CONSUMED once and allowed (a non-blocking TOOL-004 marker); otherwise it is
    recorded as pending and the blocking TOOL-003 finding names the id to approve with. With no approver it blocks as before."""
    pol = {**DEFAULT_TOOL_POLICY, **(policy or {})}
    findings: list[Finding] = []
    for tc in tool_calls or []:
        fn = tc.get("function") if isinstance(tc, dict) else None
        if not isinstance(fn, dict):
            continue
        name = str(fn.get("name") or "").strip().lower()
        args = fn.get("arguments")
        args = args if isinstance(args, str) else json.dumps(args or {})
        if pol["allow"] and not _match(name, pol["allow"]):
            findings.append(Finding("TOOL-001-not-allowed", "LLM06/ASI02", "high", f"{name} is not on the tool allow-list"))
        elif _match(name, pol["deny"]):
            findings.append(Finding("TOOL-001-denied", "LLM06/ASI02", "high", f"{name} is a denied tool"))
        elif _match(name, pol["require_approval"]):
            if approver is not None and approver.consume(name, args):
                findings.append(Finding("TOOL-004-approved", "LLM06/ASI02", "low", f"{name}: human-approved, used once"))
            else:
                pid = approver.record_pending(name, args) if approver is not None else ""
                findings.append(Finding("TOOL-003-needs-approval", "LLM06/ASI02", "high",
                                        f"{name} needs a human approval" + (f" — approve: ./securax approve {pid}" if pid else "")))
        if _DESTRUCTIVE.search(args):
            findings.append(Finding("TOOL-002-destructive-args", "LLM06/ASI02", "high", f"destructive arguments for {name}"))
        clean, leak = check_output(args, set(), canaries)
        findings += [f for f in leak if f.rule.startswith(("SECRET-", "LEAK-"))]
        clean, pii = redact_pii(args)
        findings += pii
        if pii:
            fn["arguments"] = clean
    return tool_calls, findings


def inspect_output(text: str, allowed_domains: set[str], canaries: set[str] | None = None) -> Verdict:
    clean, findings = check_output(text, allowed_domains, canaries)
    clean, pii = redact_pii(clean)
    findings += pii
    # Output is sanitised rather than blocked, unless a secret/canary leaked.
    blocked = any(f.rule.startswith(("SECRET-", "LEAK-")) for f in findings)
    return Verdict(allowed=not blocked, findings=findings, text=clean)
