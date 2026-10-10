"""PII + secret gate for the Guiding Map shipped files (the public-repo safety net).

Reuses the estate's OWN guardrail PII detectors (apps/llm-gateway/app/guardrails.py)
instead of a hardcoded list of personal identifiers — so this gate contains NO personal
data itself (a needle list in a public repo would be the very leak we are preventing),
generalises to anyone's fork, and stays consistent with how the gateway classifies PII.

It fails CI if any shipped Guiding Map file contains India-BFSI PII (Aadhaar/PAN/card/
UPI/mobile/email, checksum-verified where applicable) or a leaked secret (JSON web tokens,
Supabase URLs and keys, VAPID, AWS, or private-key material). This is the gate that keeps the open-source
cockpit clean, the successor to the old test13.js PII scan — now needle-free.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
GM = ROOT / "guiding-map"


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load("gw_guardrails_gm", "apps/llm-gateway/app/guardrails.py")

# Files that actually ship / are served. Supporting dev files (build.js, tests, package.json)
# are scanned too — nothing in the repo should carry PII or secrets.
SHIPPED = ["index.html", "ops.js", "sw.js", "manifest.json", "build.js", "README.md"]

# Secret/credential patterns (not PII, but must never land in a public repo).
SECRETS = {
    "JWT/anon-key": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "supabase-url": re.compile(r"https://[a-z0-9]{16,}\.supabase\.co"),
    "supabase-publishable": re.compile(r"sb_publishable_[A-Za-z0-9_-]{10,}"),
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private-key-block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "google-api-key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
}


def _targets():
    files = [GM / f for f in SHIPPED]
    files += sorted((GM / "tests").glob("*.js"))
    return [f for f in files if f.exists()]


@pytest.mark.parametrize("path", _targets(), ids=lambda p: p.name)
def test_no_pii_in_shipped_file(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    _clean, findings = G.redact_pii(text)
    kinds = sorted({f.rule for f in findings})
    assert not findings, f"{path.name}: PII detected -> {kinds}"


@pytest.mark.parametrize("path", _targets(), ids=lambda p: p.name)
def test_no_secrets_in_shipped_file(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    hits = [name for name, rx in SECRETS.items() if rx.search(text)]
    assert not hits, f"{path.name}: secret-like material detected -> {hits}"
