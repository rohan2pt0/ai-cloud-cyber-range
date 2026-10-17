#!/usr/bin/env python3
"""The BFSI control library: every RBI / SEBI / IRDAI / IFSCA / NCIIPC / CERT-In / DPDP obligation as one set of controls,
with per-class applicability, citations, evidence and audit tests, and a visual navigator for it.

    ./securax controls import WORKBOOK.xlsx    read the gap-assessment workbook into vault/controls/library.json (private)
    ./securax controls profile [CLASS]         what applies: the CEILING (strictest of all 22 classes) or one class
    ./securax controls dominance               which classes are fully covered by complying with SCB/PSB (and the exceptions)
    ./securax controls navigator               write portal/navigator.html (+ one page per class): grid, radar, heat map
    ./securax controls gaps [CLASS]            the vital few: critical MUST controls not proven and below target

The library is PRIVATE: it stays in vault/ (never in git). New regulations are added as packs in governance/controls/packs/
(JSON: new controls, or extra citations for existing ones) or by importing a newer workbook; nothing in code changes.
Your maturity scores are read from the workbook's yellow cells (Current / Target maturity, Likelihood, Impact) on import.
What SecuRAX itself proves per control is in governance/controls/securax-map.json, each entry with real evidence files.
Standard library only (the .xlsx reader included). Exit codes: 0 ok, 1 nothing to show / a problem, 2 bad usage.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB = ROOT / "vault" / "controls" / "library.json"
PACKS = ROOT / "governance" / "controls" / "packs"
SXMAP = ROOT / "governance" / "controls" / "securax-map.json"
OUT = ROOT / "portal" / "navigator.html"
RANK = {"MUST": 3, "SHOULD": 2, "MAY": 1, "N/A": 0, "": 0}
LEVEL = {v: k for k, v in RANK.items() if k}
TIER_W = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}
CEILING = "Ceiling (strictest of all classes)"
DOMAINS = {"GOV": "Governance", "RM": "Risk management", "IAM": "Identity & access", "AM": "Asset management",
           "DP": "Data protection", "NS": "Network security", "EP": "Endpoint", "AS": "Application security", "CL": "Cloud",
           "TP": "Third parties", "CR": "Cryptography & PQC", "VM": "Vulnerability mgmt", "SOC": "Security operations",
           "IR": "Incident response", "BCP": "Resilience & BCP", "PS": "Physical", "HR": "People", "AW": "Awareness",
           "AUD": "Audit & assurance", "ET": "Emerging tech & AI"}
REGULATORS = [("RBI", ("RBI Primary Citation", "RBI Secondary Citation")), ("SEBI", ("SEBI CSCRF",)), ("IRDAI", ("IRDAI 2023",)),
              ("IFSCA", ("IFSCA 2025",)), ("NPCI / PCI / SWIFT", ("NPCI / PCI DSS / SWIFT",)), ("NCIIPC / CERT-In / DPDP", ("NCIIPC / CERT-In / DPDP",)),
              ("NSCS audit baseline (pack)", ("NSCS Audit Baseline 2020",)), ("NCIIPC CII framework (pack)", ("NCIIPC CII Framework",))]
_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


# ---------------------------------------------------------------------------------------------------- .xlsx (stdlib)
def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path: pathlib.Path) -> dict[str, list[list]]:
    """{sheet name: rows of cell values}. Cached formula results are used; document properties are never read."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        out = {}
        for s in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", _NS):
            target = rels[s.get(f"{{{_NS['r']}}}id")].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            rows = []
            for row in ET.fromstring(z.read(target)).iter(f"{{{_NS['m']}}}row"):
                vals: list = []
                for c in row.findall("m:c", _NS):
                    i, t = _col(c.get("r")), c.get("t")
                    v = c.find("m:v", _NS)
                    if t == "s" and v is not None:
                        val = shared[int(v.text)]
                    elif t == "inlineStr":
                        val = "".join(x.text or "" for x in c.iter(f"{{{_NS['m']}}}t"))
                    else:
                        val = v.text if v is not None else None
                    vals += [None] * (i - len(vals) + 1) if i >= len(vals) else []
                    vals[i] = val
                rows.append(vals)
            out[s.get("name")] = rows
        return out


def _num(v):
    try:
        f = float(v)
        return int(f) if f == int(f) else f
    except (TypeError, ValueError):
        return None


def _table(rows: list[list], first: str) -> list[dict]:
    """Rows under the header row whose first cell is `first`, as dicts."""
    for i, r in enumerate(rows):
        if r and str(r[0] or "").strip() == first:
            head = [str(h or "").strip() for h in r]
            return [dict(zip(head, x + [None] * (len(head) - len(x)))) for x in rows[i + 1:] if x and x[0]]
    return []


def import_workbook(path: pathlib.Path) -> dict:
    sheets = read_xlsx(path)
    cat = next((v for k, v in sheets.items() if "Master Catalogue" in k), None)
    if cat is None:
        raise SystemExit("not a gap-assessment workbook: no 'Master Catalogue' sheet")
    rows = _table(cat, "Control ID")
    head = [str(h or "").strip() for h in next(r for r in cat if r and str(r[0] or "").strip() == "Control ID")]
    classes = head[head.index("Residual Risk") + 1:] if "Residual Risk" in head else []
    regcols = [c for _, cols in REGULATORS for c in cols]
    fw = ["NIST CSF 2.0 sub-cat", "ISO 27001/22301/etc.", "CIS Controls v8.1", "Other Global (DORA/MAS/BCBS)"]
    controls = []
    for r in rows:
        cid = str(r["Control ID"]).strip()
        if not re.fullmatch(r"[A-Z]{2,4}-\d{3}", cid):
            continue
        controls.append({
            "id": cid, "domain": str(r.get("Domain") or "").strip(), "subdomain": r.get("Sub-Domain") or "",
            "title": r.get("Control Title") or "", "description": r.get("Control Description") or "",
            "tier": r.get("Criticality Tier") or "", "mitre": (r.get("Threat (MITRE ATT&CK)") or "").strip(" -"),
            "citations": {c: r.get(c) for c in regcols if r.get(c) not in (None, "", "-")},
            "frameworks": {c: r.get(c) for c in fw if r.get(c) not in (None, "", "-")},
            "evidence": r.get("Evidence Required") or "", "test": r.get("Audit Test Procedure") or "",
            "remediation": r.get("Remediation Action") or "", "owner": r.get("Owner Function") or "",
            "ppt": r.get("People / Process / Tech") or "", "cost": r.get("Indicative Cost (INR)") or "", "timeline": r.get("Timeline") or "",
            "applicability": {c: str(r.get(c) or "N/A").strip().upper() for c in classes},
            "assessment": {"current": _num(r.get("Current Maturity (0-5)")), "target": _num(r.get("Target Maturity (0-5)")),
                           "likelihood": _num(r.get("Likelihood (1-5)")), "impact": _num(r.get("Impact (1-5)"))},
        })
    cover = next((v for k, v in sheets.items() if "Cover" in k), [])
    version = next((str(r[0]) for r in cover[:6] if r and r[0] and re.search(r"\bv\d", str(r[0]))), "")
    return {"meta": {"source": path.name, "version": version, "imported": dt.date.today().isoformat(), "controls": len(controls)},
            "classes": classes, "controls": controls}


# ---------------------------------------------------------------------------------------------------- library + packs
def load(lib: pathlib.Path | None = None, packs: pathlib.Path | None = None) -> dict | None:
    lib, packs = lib or LIB, packs or PACKS
    try:
        data = json.loads(lib.read_text("utf-8"))
    except (OSError, ValueError):
        return None
    by_id = {c["id"]: c for c in data["controls"]}
    for p in sorted(packs.glob("*.json")) if packs.is_dir() else []:
        pack = json.loads(p.read_text("utf-8"))
        for c in pack.get("controls", []):                       # a new control (a new regulation), or an override
            c.setdefault("applicability", {k: "MUST" for k in data["classes"]})
            c.setdefault("assessment", {})
            c.setdefault("citations", {})
            by_id[c["id"]] = {**by_id.get(c["id"], {}), **c, "pack": p.name}
        for cid, cites in pack.get("citations", {}).items():     # an extra citation on an existing control
            if cid in by_id:
                by_id[cid].setdefault("citations", {}).update(cites)
    data["controls"] = sorted(by_id.values(), key=lambda c: (list(DOMAINS).index(c["domain"]) if c["domain"] in DOMAINS else 99, c["id"]))
    return data


def ceiling(c: dict) -> str:
    return LEVEL.get(max((RANK.get(v, 0) for v in c["applicability"].values()), default=0), "N/A")


def level(c: dict, cls: str) -> str:
    return ceiling(c) if cls == CEILING else c["applicability"].get(cls, "N/A")


def dominance(data: dict, top: str = "SCB/PSB") -> dict[str, list[str]]:
    """For each class: the controls where it is STRICTER than `top`, i.e. what complying with `top` alone would miss."""
    return {cls: [c["id"] for c in data["controls"] if RANK.get(c["applicability"].get(cls, ""), 0) > RANK.get(c["applicability"].get(top, ""), 0)]
            for cls in data["classes"]}


def sx_map(path: pathlib.Path | None = None) -> dict:
    try:
        return json.loads((path or SXMAP).read_text("utf-8"))["controls"]
    except (OSError, ValueError, KeyError):
        return {}


def state(c: dict, sx: dict) -> str:
    """The cell colour: your own maturity when you scored it, else what SecuRAX proves, else 'org' (the organisation's)."""
    a = c.get("assessment") or {}
    if a.get("current") is not None and a.get("target") is not None:
        gap = a["target"] - a["current"]
        return "met" if gap <= 0 else ("near" if gap == 1 else "far")
    return {"proven": "proven", "partial": "partial"}.get(sx.get(c["id"], {}).get("status"), "org")


def _risks():
    """The private risk register (governance/risks.py), loaded lazily; (risks, module) or ([], None) when there is none."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("risks", ROOT / "governance" / "risks.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.load(), mod
    except Exception:  # noqa: BLE001 - the register is optional
        return [], None


def vital_gaps(data: dict, cls: str, sx: dict, n: int = 10, pressure: dict | None = None) -> list[dict]:
    """80/20: applicable MUST controls that are critical or high, not proven and not at target, worst first."""
    out = []
    for c in data["controls"]:
        if level(c, cls) != "MUST" or state(c, sx) in ("met", "proven"):
            continue
        a = c.get("assessment") or {}
        risk = max((a.get("likelihood") or 0) * (a.get("impact") or 0), (pressure or {}).get(c["id"], 0))   # your score, or your open risks
        breadth = sum(1 for v in c["applicability"].values() if v == "MUST")   # MUST for many classes = closes many gaps at once
        out.append((TIER_W.get(c["tier"], 0), risk, breadth, (a.get("target") or 0) - (a.get("current") or 0), c))
    out.sort(key=lambda t: (-t[0], -t[1], -t[2], -t[3], t[4]["id"]))
    return [t[4] for t in out[:n]]


# ---------------------------------------------------------------------------------------------------- the navigator page
E = html.escape
CSS = """
:root{--bg:#0b1016;--card:#121a23;--ink:#e6edf3;--mut:#8b98a6;--line:#25313d;--g:#3fb950;--a:#d29922;--r:#f85149;--b:#58a6ff;--u:#3a4652;--na:#1a222b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1400px;margin:0 auto;padding:14px}a{color:var(--b)}h1{font-size:1.3rem;margin:.1rem 0}h2{font-size:1rem;margin:0 0 .5rem;letter-spacing:.04em;text-transform:uppercase;color:var(--mut)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.annun{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}
.lamp{border:1px solid var(--line);border-radius:8px;padding:10px;background:#0e151d}.lamp b{display:block;font-size:1.6rem}
.lamp.warn{border-color:var(--r);background:#2a1214}.lamp.caut{border-color:var(--a);background:#2a2110}.lamp.ok b{color:var(--g)}
.lamp.warn b{color:var(--r)}.lamp.caut b{color:var(--a)}.muted{color:var(--mut)}code{background:#0e151d;border:1px solid var(--line);border-radius:5px;padding:0 5px}
.nav{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(76px,1fr);gap:4px;overflow-x:auto}
.col h3{font-size:.72rem;margin:0 0 4px;color:var(--mut);text-align:center;min-height:2.6em}.cell{display:block;font-size:.66rem;padding:3px 2px;margin:0 0 3px;border-radius:3px;text-align:center;color:#fff;text-decoration:none;border:1px solid transparent}
.cell.proven,.cell.met{background:#1f6f3b}.cell.partial,.cell.near{background:#7a5a12}.cell.far{background:#8e2a24}.cell.org{background:var(--u)}
.cell.na{background:var(--na);color:#4b5866}.cell.crit{border-color:#fff}.cell.should{opacity:.82}.cell.may{opacity:.6}
.legend span{display:inline-flex;align-items:center;gap:5px;margin-right:14px}.legend i{width:14px;height:14px;border-radius:3px;display:inline-block}
.two{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.hm{border-collapse:collapse}.hm td,.hm th{width:58px;height:40px;text-align:center;border:1px solid var(--line);font-size:.85rem}
.bar{height:12px;border-radius:3px;background:var(--g);display:inline-block;vertical-align:middle}.bar.p{background:var(--a)}.bar.o{background:var(--u)}
table.t{border-collapse:collapse;width:100%}table.t td,table.t th{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}
.profiles a{display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;border:1px solid var(--line);border-radius:99px;text-decoration:none;font-size:.8rem}.profiles a.on{background:var(--b);color:#000}
svg text{fill:var(--ink);font-size:11px}svg .ring{fill:none;stroke:var(--line)}svg .sp{stroke:var(--line)}
svg .s-t{fill:none;stroke:var(--mut);stroke-dasharray:4 3}svg .s-sx{fill:rgba(88,166,255,.25);stroke:var(--b)}svg .s-me{fill:rgba(63,185,80,.25);stroke:var(--g)}
"""


def slug(cls: str) -> str:
    return "ceiling" if cls == CEILING else re.sub(r"[^a-z0-9]+", "-", cls.lower()).strip("-")


def domain_scores(data: dict, cls: str, sx: dict) -> list[dict]:
    rows = []
    for d, name in DOMAINS.items():
        cs = [c for c in data["controls"] if c["domain"] == d and level(c, cls) != "N/A"]
        if not cs:
            continue
        sxv = sum({"proven": 5, "partial": 2.5}.get(sx.get(c["id"], {}).get("status"), 0) for c in cs) / len(cs)
        cur = [c["assessment"]["current"] for c in cs if (c.get("assessment") or {}).get("current") is not None]
        tgt = [c["assessment"]["target"] for c in cs if (c.get("assessment") or {}).get("target") is not None]
        rows.append({"code": d, "name": name, "n": len(cs), "sx": round(sxv, 2), "me": round(sum(cur) / len(cur), 2) if cur else None,
                     "target": round(sum(tgt) / len(tgt), 2) if tgt else 3.0})
    return rows


def radar(rows: list[dict]) -> str:
    if len(rows) < 3:
        return "<p class='muted'>Not enough domains.</p>"
    cx, cy, R, n = 330, 300, 220, len(rows)

    def pt(i, v):
        a = -math.pi / 2 + 2 * math.pi * i / n
        return cx + R * v / 5 * math.cos(a), cy + R * v / 5 * math.sin(a)

    def poly(vals):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, v) for i, v in enumerate(vals)))
    g = [f"<polygon class='ring' points='{poly([k] * n)}'/>" for k in range(1, 6)]
    for i, r in enumerate(rows):
        x, y = pt(i, 5)
        lx, ly = pt(i, 5.45)
        g.append(f"<line class='sp' x1='{cx}' y1='{cy}' x2='{x:.1f}' y2='{y:.1f}'/>")
        anchor = "middle" if abs(lx - cx) < 12 else ("start" if lx > cx else "end")
        g.append(f"<text x='{lx:.1f}' y='{ly:.1f}' text-anchor='{anchor}'><title>{E(r['name'])}: {r['n']} controls</title>{E(r['code'])}</text>")
    g.append(f"<polygon class='s-t' points='{poly([r['target'] for r in rows])}'/>")
    g.append(f"<polygon class='s-sx' points='{poly([r['sx'] for r in rows])}'/>")
    if any(r["me"] is not None for r in rows):
        g.append(f"<polygon class='s-me' points='{poly([r['me'] or 0 for r in rows])}'/>")
    return f"<svg viewBox='0 0 660 610' role='img' aria-label='Maturity by domain, 0 to 5'>{''.join(g)}</svg>"


def heatmap(data: dict, cls: str, risks: list | None = None) -> str:
    cells = [[0] * 5 for _ in range(5)]
    scored, source = 0, "controls you scored"
    for c in data["controls"]:
        a = c.get("assessment") or {}
        if level(c, cls) != "N/A" and a.get("likelihood") and a.get("impact"):
            cells[5 - int(a["impact"])][int(a["likelihood"]) - 1] += 1
            scored += 1
    if not scored and risks:                                   # no control scores yet: plot the open risks from the register
        for r in risks:
            li, im = r.get("likelihood"), r.get("impact")
            if li and im and 1 <= li <= 5 and 1 <= im <= 5 and not (r.get("done") or re.search(r"closed|completed|done|resolved", r.get("status") or "", re.I)):
                cells[5 - int(round(im))][int(round(li)) - 1] += 1
                scored += 1
        source = "open risks in your risk register (./securax risks list --open)"
    if not scored:
        return ("<p class='muted'>No likelihood × impact scores yet. Fill the yellow <b>Likelihood</b> and <b>Impact</b> cells in the workbook, "
                "then <code>./securax controls import WORKBOOK.xlsx</code>: this 5 × 5 map fills itself.</p>")
    h = ["<table class='hm'><tr><th>Impact ↓ / Likelihood →</th>" + "".join(f"<th>{i}</th>" for i in range(1, 6)) + "</tr>"]
    for ri, row in enumerate(cells):
        imp = 5 - ri
        tds = []
        for li, n in enumerate(row, 1):
            s = imp * li
            col = "#8e2a24" if s >= 20 else "#7a3a12" if s >= 12 else "#7a5a12" if s >= 6 else "#1f6f3b"
            tds.append(f"<td style='background:{col}'>{n or ''}</td>")
        h.append(f"<tr><th>{imp}</th>{''.join(tds)}</tr>")
    return "".join(h) + f"</table><p class='muted'>From {E(source)}. Score = likelihood × impact: 20–25 critical (30 days), 12–19 high (90 days), 6–11 medium, 1–5 low.</p>"


def regulator_bars(data: dict, cls: str, sx: dict) -> str:
    out = ["<table class='t'><tr><th>Regulator</th><th>Applicable controls citing it</th><th>SecuRAX proves / partly / organisation's</th></tr>"]
    for name, cols in REGULATORS:
        cs = [c for c in data["controls"] if level(c, cls) != "N/A" and any(col in c.get("citations", {}) for col in cols)]
        if not cs:
            continue
        p = sum(1 for c in cs if sx.get(c["id"], {}).get("status") == "proven")
        q = sum(1 for c in cs if sx.get(c["id"], {}).get("status") == "partial")
        o = len(cs) - p - q
        w = lambda k: f"{k / len(cs) * 260:.0f}"
        out.append(f"<tr><td>{E(name)}</td><td>{len(cs)}</td><td><span class='bar' style='width:{w(p)}px'></span><span class='bar p' style='width:{w(q)}px'></span>"
                   f"<span class='bar o' style='width:{w(o)}px'></span> <span class='muted'>{p} / {q} / {o}</span></td></tr>")
    return "".join(out) + "</table>"


def page(data: dict, cls: str, sx: dict, dom: dict, risks: list | None = None, rmod=None) -> str:
    app = [c for c in data["controls"] if level(c, cls) != "N/A"]
    must = [c for c in app if level(c, cls) == "MUST"]
    crit_open = [c for c in must if c["tier"] == "Critical" and state(c, sx) not in ("met", "proven")]
    proven = sum(1 for c in app if state(c, sx) in ("proven", "met"))
    scored = sum(1 for c in app if (c.get("assessment") or {}).get("current") is not None)
    risks = risks or []
    pressure = rmod.control_pressure(risks) if rmod else {}
    late = rmod.overdue(risks) if rmod else []
    gaps = vital_gaps(data, cls, sx, pressure=pressure)
    misses = [] if cls == CEILING else dom.get(cls, []) if cls != "SCB/PSB" else []
    stamp = dt.datetime.now().strftime("%d %b %Y %H:%M")
    h = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>Control navigator · {E(cls)}</title><style>{CSS}</style></head><body><main>"]
    h.append(f"<div class='muted'>SecuRAX control navigator · {E(data['meta'].get('version') or data['meta']['source'])} · imported {E(data['meta']['imported'])} · "
             f"page {E(stamp)} · <a href='/portal/cockpit.html'>Cockpit</a> · <a href='/hub.html'>All apps</a></div>")
    h.append(f"<h1>{E(cls)}: {len(app)} controls apply, {len(must)} of them MUST</h1>")
    # Master caution / warning panel: lamps light only when something is abnormal (the dark-cockpit rule).
    lamps = [("warn" if crit_open else "ok", len(crit_open), "Critical MUST controls not proven or at target"),
             ("caut" if gaps else "ok", len(gaps), "Vital few to close next (below)"),
             ("ok" if proven else "caut", proven, f"Proven or at target (of {len(app)})"),
             ("caut" if not scored else "ok", scored, "Controls you have scored"),
             ("warn" if misses else "ok", len(misses), "Stricter here than SCB/PSB" if cls != CEILING else "Ceiling: covers every class"),
             ("warn" if late else "ok", len(late), "Risk treatments overdue (./securax risks overdue)")]
    h.append("<div class='card'><h2>Master caution</h2><div class='annun'>" + "".join(
        f"<div class='lamp {k}'><b>{v}</b>{E(t)}</div>" for k, v, t in lamps) + "</div></div>")
    profiles = [CEILING] + data["classes"]
    h.append("<div class='card'><h2>Profile</h2><div class='profiles'>" + "".join(
        f"<a class='{'on' if p == cls else ''}' href='/portal/navigator/{slug(p)}.html'>{E(p)}</a>" for p in profiles) + "</div>"
        "<p class='muted'>The <b>ceiling</b> takes the strictest requirement for each control across all classes, so meeting it meets every class. "
        "SCB/PSB alone is not enough for every class: see the exceptions table below.</p></div>")
    if gaps:
        h.append("<div class='card'><h2>The vital few (80/20)</h2><table class='t'><tr><th>Control</th><th>Tier</th><th>Why it matters</th><th>Owner</th></tr>" + "".join(
            f"<tr><td><b>{E(c['id'])}</b> {E(c['title'])}</td><td>{E(c['tier'])}</td><td class='muted'>{E(str(c.get('remediation') or c.get('description'))[:160])}</td><td>{E(c.get('owner') or '')}</td></tr>"
            for c in gaps) + "</table></div>")
    # MITRE-style navigator grid: one column per domain, one cell per control.
    cols = []
    for d, name in DOMAINS.items():
        cs = [c for c in data["controls"] if c["domain"] == d]
        if not cs:
            continue
        cells = []
        for c in cs:
            lv = level(c, cls)
            st = "na" if lv == "N/A" else state(c, sx)
            cl = f"cell {st}" + (" crit" if c["tier"] == "Critical" else "") + (" should" if lv == "SHOULD" else " may" if lv == "MAY" else "")
            cite = "; ".join(f"{k}: {v}" for k, v in list(c.get("citations", {}).items())[:3])
            ev = sx.get(c["id"], {})
            tip = (f"{c['id']} {c['title']} | {lv} for {cls} | tier {c['tier']} | "
                   + (f"SecuRAX {ev['status']}: {ev.get('note', '')} | " if ev else "the organisation's | ") + cite)
            cells.append(f"<span class='{cl}' title='{E(tip)}'>{E(c['id'].split('-')[1])}</span>")
        cols.append(f"<div class='col'><h3>{E(name)}<br>{E(d)}</h3>{''.join(cells)}</div>")
    h.append("<div class='card'><h2>Navigator</h2><div class='legend muted'>"
             "<span><i style='background:#1f6f3b'></i>proven by SecuRAX / at your target</span><span><i style='background:#7a5a12'></i>partly / 1 level short</span>"
             "<span><i style='background:#8e2a24'></i>2+ levels short</span><span><i style='background:var(--u)'></i>the organisation's (people, process, contracts)</span>"
             "<span><i style='background:var(--na)'></i>not applicable</span><span><i style='background:var(--u);border:1px solid #fff'></i>white edge = Critical</span>"
             "<span>faded = SHOULD / MAY</span></div><p class='muted'>Hover a cell for the title, requirement, SecuRAX evidence and citations.</p>"
             f"<div class='nav'>{''.join(cols)}</div></div>")
    rows = domain_scores(data, cls, sx)
    h.append("<div class='two'><div class='card'><h2>Maturity by domain</h2><div class='legend muted'><span><i style='border:1px dashed var(--mut)'></i>target</span>"
             "<span><i style='background:rgba(88,166,255,.5)'></i>what SecuRAX proves</span><span><i style='background:rgba(63,185,80,.5)'></i>your scored maturity</span></div>"
             f"{radar(rows)}</div><div class='card'><h2>Risk heat map (5 × 5)</h2>{heatmap(data, cls, risks)}</div></div>")
    h.append(f"<div class='card'><h2>Regulators</h2>{regulator_bars(data, cls, sx)}</div>")
    exc = {k: v for k, v in dom.items() if v}
    h.append("<div class='card'><h2>Does complying with SCB/PSB cover the others?</h2>"
             + ("<p>For these classes, SCB/PSB compliance alone leaves controls uncovered (they are stricter there):</p><table class='t'>"
                + "".join(f"<tr><td>{E(k)}</td><td>{', '.join(E(i) for i in v)}</td></tr>" for k, v in exc.items()) + "</table>"
                if exc else "<p>Yes: no class is stricter than SCB/PSB on any control.</p>")
             + "<p class='muted'>The ceiling profile includes these, so meeting the ceiling covers every class.</p></div>")
    h.append("<div class='card muted'>Colours show your own maturity score where you entered one, otherwise what SecuRAX proves with evidence "
             "(<code>governance/controls/securax-map.json</code>). Grey is not a failure: it marks a duty only the organisation can meet. "
             "This page is a self-assessment aid, not an audit opinion. No script, no external request.</div></main></body></html>")
    return "".join(h)


def write_navigator(data: dict, out: pathlib.Path | None = None) -> list[pathlib.Path]:
    out = out or OUT
    sx, dom = sx_map(), dominance(data)
    risks, rmod = _risks()
    written = []
    (out.parent / "navigator").mkdir(parents=True, exist_ok=True)
    for cls in [CEILING] + data["classes"]:
        p = out.parent / "navigator" / f"{slug(cls)}.html"
        p.write_text(page(data, cls, sx, dom, risks, rmod), "utf-8")
        written.append(p)
    out.write_text(page(data, CEILING, sx, dom, risks, rmod), "utf-8")
    return [out] + written


# ---------------------------------------------------------------------------------------------------- CLI
def _need() -> dict:
    data = load()
    if not data:
        raise SystemExit("No control library yet. Import your workbook first:  ./securax controls import WORKBOOK.xlsx")
    return data


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "help"
    if cmd == "import" and len(argv) == 2:
        data = import_workbook(pathlib.Path(argv[1]))
        LIB.parent.mkdir(parents=True, exist_ok=True)
        LIB.write_text(json.dumps(data, indent=1, ensure_ascii=False), "utf-8")
        try:
            LIB.chmod(0o600)
        except OSError:
            pass
        scored = sum(1 for c in data["controls"] if c["assessment"].get("current") is not None)
        print(f"✔ {data['meta']['controls']} controls, {len(data['classes'])} classes imported into {LIB.relative_to(ROOT)} (private; {scored} scored)")
        for p in write_navigator(load())[:1]:
            print(f"✔ navigator: {p.relative_to(ROOT)}  (http://localhost:8088/portal/navigator.html)")
        return 0
    if cmd == "profile":
        data, cls = _need(), " ".join(argv[1:]) or CEILING
        if cls != CEILING and cls not in data["classes"]:
            print("classes: " + ", ".join(data["classes"]))
            return 2
        counts = {}
        for c in data["controls"]:
            counts[level(c, cls)] = counts.get(level(c, cls), 0) + 1
        print(f"{cls}: " + ", ".join(f"{counts.get(k, 0)} {k}" for k in ("MUST", "SHOULD", "MAY", "N/A")))
        return 0
    if cmd == "dominance":
        for cls, ids in dominance(_need()).items():
            print(f"{'✔' if not ids else '✗'} {cls:<16} " + ("covered by SCB/PSB" if not ids else "stricter than SCB/PSB on " + ", ".join(ids)))
        print("The ceiling profile (./securax controls profile) covers every class.")
        return 0
    if cmd == "navigator":
        ps = write_navigator(_need())
        print(f"✔ wrote {len(ps)} pages; open http://localhost:8088/portal/navigator.html")
        return 0
    if cmd == "gaps":
        data, cls = _need(), " ".join(argv[1:]) or CEILING
        for c in vital_gaps(data, cls, sx_map()):
            print(f"{c['id']:<8} {c['tier']:<9} {c['title']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
