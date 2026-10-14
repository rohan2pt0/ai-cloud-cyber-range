"""Offline threat-intel enrichment for the AI-SOC and `./securax scan`.

Reads the snapshots `./securax offline sync` keeps in ~/.securax/intel (CISA KEV, MITRE ATT&CK). It NEVER touches the network:
no snapshot → no enrichment and a clear note, never an error. Standard library only.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import time

TECH = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")
CVE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.I)


def intel_dir() -> pathlib.Path:
    home = os.environ.get("SECURAX_HOME_DIR") or os.path.join(os.path.expanduser("~"), ".securax")
    return pathlib.Path(home) / "intel"


def _load(name: str) -> dict:
    try:
        return json.loads((intel_dir() / f"{name}.json").read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def age_days(snapshot: dict) -> float | None:
    ts = snapshot.get("fetched_at")
    return None if not ts else max(0.0, (time.time() - ts) / 86400)


def attack_techniques(text: str) -> list[dict]:
    """Technique ids found in free text ('T1190 (exploit public app)', 'T1059 / T1552') → name + tactics. Unknown ids are kept as-is."""
    snap = _load("attack")
    known = snap.get("techniques", {})
    out = []
    for tid in dict.fromkeys(TECH.findall(text or "")):
        t = known.get(tid)
        out.append({"id": tid, "name": t["name"] if t else None, "tactics": t["tactics"] if t else [], "url": f"https://attack.mitre.org/techniques/{tid.replace('.', '/')}/"})
    return out


def enrich_incident(inc: dict) -> dict:
    """Add `techniques` (from the ATT&CK snapshot) to an incident dict. Harmless when there is no snapshot."""
    inc["techniques"] = attack_techniques(f"{inc.get('attack', '')} {inc.get('atlas', '')}")
    return inc


def kev_lookup(cves: list[str]) -> dict[str, dict]:
    snap = _load("kev").get("by_cve", {})
    return {c.upper(): snap[c.upper()] for c in cves if c.upper() in snap}


def kev_report(text: str) -> dict:
    """Which CVE ids in `text` (e.g. Trivy output) are known to be exploited in the wild? Also reports how stale the snapshot is."""
    snap = _load("kev")
    ids = list(dict.fromkeys(c.upper() for c in CVE.findall(text or "")))
    hits = kev_lookup(ids)
    return {"cves_seen": len(ids), "snapshot": bool(snap), "age_days": age_days(snap), "snapshot_count": snap.get("count", 0),
            "exploited": [{"cve": c, **v} for c, v in sorted(hits.items(), key=lambda kv: kv[1].get("due", ""))]}


def render_kev(rep: dict) -> str:
    if not rep["snapshot"]:
        return "KEV check skipped: no CISA KEV snapshot yet. Run `./securax offline sync` once while online; after that this works offline."
    stale = f" (snapshot is {rep['age_days']:.0f} days old: refresh with `./securax offline sync` when online)" if (rep["age_days"] or 0) > 7 else ""
    if not rep["exploited"]:
        return f"KEV check: none of the {rep['cves_seen']} CVE(s) above is in CISA's known-exploited list{stale}."
    lines = [f"KEV check: {len(rep['exploited'])} of {rep['cves_seen']} CVE(s) are KNOWN-EXPLOITED in the wild — fix these first{stale}:"]
    for e in rep["exploited"]:
        ransom = "  [used in ransomware]" if str(e.get("ransomware", "")).lower() == "known" else ""
        lines.append(f"  • {e['cve']}  {e.get('vendor', '')} {e.get('product', '')} — {e.get('name', '')}  (CISA due {e.get('due', '?')}){ransom}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "kev":
        print(render_kev(kev_report(sys.stdin.read())))
    elif len(sys.argv) > 2 and sys.argv[1] == "technique":
        print(json.dumps(attack_techniques(" ".join(sys.argv[2:])), indent=2))
    else:
        sys.exit("usage: enrich.py kev < scan-output   |   enrich.py technique T1190 T1059.001")
