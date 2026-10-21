#!/usr/bin/env python3
"""The BFSI control library: every RBI / SEBI / IRDAI / IFSCA / CII / CERT-In / DPDP obligation as one set of controls,
with per-class applicability, citations, evidence and audit tests, and a visual navigator for it.

    ./securax controls import [WORKBOOK.xlsx]  read the gap-assessment workbook into vault/controls/library.json (private). No path, a
                                               wrong one or a folder: it finds the workbook in Downloads/Documents/Desktop/vault/inbox
    ./securax controls auto                    import it only if a newer workbook is there (./securax go runs this)
    ./securax controls profile [CLASS]         what applies: the CEILING (strictest of all 22 classes) or one class
    ./securax controls dominance               which classes are fully covered by complying with the first class (SCB/PSB in your workbook) and the exceptions
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
import importlib.util
import json
import math
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile


def _addr():
    """governance/addr.py, loaded by path (this module is itself loaded by path in tests): the address a person opens."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_addr", pathlib.Path(__file__).resolve().parent / "addr.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB = ROOT / "vault" / "controls" / "library.json"
PACKS = ROOT / "governance" / "controls" / "packs"
STARTER = ROOT / "governance" / "controls" / "starter.json"       # public, plain-words library used until you import your own workbook
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
              ("IFSCA", ("IFSCA 2025",)), ("NPCI / PCI / SWIFT", ("NPCI / PCI DSS / SWIFT",)), ("CII / CERT-In / DPDP", ("CII / CERT-In / DPDP",)),
              ("NSCS audit baseline (pack)", ("NSCS Audit Baseline 2020",)), ("National CII guidance (pack)", ("CII Framework",)),
              ("RBI model risk draft 2026 (pack)", ("RBI MRM draft 2026",)),
              ("RBI Payments Vision 2028 (pack)", ("RBI Payments Vision 2028",))]
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


def sheet_names(path: pathlib.Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as z:
            return [s.get("name") or "" for s in ET.fromstring(z.read("xl/workbook.xml")).find("m:sheets", _NS)]
    except (OSError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError):
        return []


def search_dirs(home: pathlib.Path | None = None, win: pathlib.Path = pathlib.Path("/mnt/c/Users")) -> list[pathlib.Path]:
    """Where people keep downloaded workbooks: Downloads, Documents, Desktop, here, the private inbox, and the Windows ones on WSL."""
    home = home or pathlib.Path.home()
    ds = [home / d for d in ("Downloads", "Documents", "Desktop")] + [ROOT / "vault" / "inbox", pathlib.Path.cwd()]
    try:
        ds += [u / d for u in sorted(win.iterdir()) for d in ("Downloads", "Documents", "Desktop", "OneDrive/Documents", "OneDrive/Desktop")]
    except OSError:
        pass
    return [d for d in ds if d.is_dir()]


def find_xlsx(dirs: list[pathlib.Path] | None = None) -> list[pathlib.Path]:
    """Every .xlsx directly in those folders, newest first (Excel's own ~$ lock files skipped)."""
    out: dict[pathlib.Path, float] = {}
    for d in search_dirs() if dirs is None else dirs:
        try:
            for f in d.glob("*.xlsx"):
                if not f.name.startswith("~$") and f.is_file():
                    out[f.resolve()] = f.stat().st_mtime
        except OSError:
            continue
    return sorted(out, key=out.get, reverse=True)


def is_library_workbook(path: pathlib.Path) -> bool:
    return any("Master Catalogue" in n for n in sheet_names(path))


def confirm(found: list[pathlib.Path], what: str) -> list[pathlib.Path]:
    """No path given: show what was found and ask once, so nobody has to type a path."""
    if not found:
        print(f"No {what} found in Downloads, Documents or Desktop (the Windows ones too).")
        print("Save the .xlsx file to Downloads and run this again, or give its path after 'import'.")
        return []
    print(f"Found {len(found)} {what}:")
    for f in found:
        print(f"  {f}")
    if not sys.stdin.isatty():
        print("Run again with the file's path after 'import' to import it.")
        return []
    try:
        ans = input(("Import it" if len(found) == 1 else "Import them") + "? [Y/n]: ")
    except EOFError:
        ans = "n"
    return [] if ans.strip().lower().startswith("n") else found


def _num(v):
    try:
        f = float(v)
        return int(f) if f == int(f) else f
    except (TypeError, ValueError):
        return None


# A workbook or an older library may name the national CII agency in a column title; the public code keeps the neutral name.
_OLD_KEYS = ((re.compile(r"^[A-Z]{3,10} / CERT-In / DPDP$"), "CII / CERT-In / DPDP"), (re.compile(r"^[A-Z]{3,10} CII Framework$"), "CII Framework"))


def neutral(key: str) -> str:
    """The neutral column name for a citation column (an agency's name in the title becomes 'CII')."""
    for rx, new in _OLD_KEYS:
        if rx.match(key):
            return new
    return key


def _table(rows: list[list], first: str) -> list[dict]:
    """Rows under the header row whose first cell is `first`, as dicts."""
    for i, r in enumerate(rows):
        if r and str(r[0] or "").strip() == first:
            head = [neutral(str(h or "").strip()) for h in r]
            return [dict(zip(head, x + [None] * (len(head) - len(x)))) for x in rows[i + 1:] if x and x[0]]
    return []


def import_workbook(path: pathlib.Path) -> dict:
    sheets = read_xlsx(path)
    cat = next((v for k, v in sheets.items() if "Master Catalogue" in k), None)
    if cat is None:
        raise SystemExit("not a gap-assessment workbook: no 'Master Catalogue' sheet")
    rows = _table(cat, "Control ID")
    head = [neutral(str(h or "").strip()) for h in next(r for r in cat if r and str(r[0] or "").strip() == "Control ID")]
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
def starter(path: pathlib.Path | None = None) -> dict:
    """The public starter library. Which class a control applies to follows its tier: Critical is MUST for everyone; High is MUST for
    larger entities and SHOULD for the smaller ones; Medium is SHOULD (MAY for smaller ones); Low is MAY."""
    data = json.loads((path or STARTER).read_text("utf-8"))
    small = set(data.pop("smaller", []))
    rule = {"Critical": ("MUST", "MUST"), "High": ("MUST", "SHOULD"), "Medium": ("SHOULD", "MAY"), "Low": ("MAY", "MAY")}
    for c in data["controls"]:
        big, little = rule.get(c.get("tier"), ("MAY", "MAY"))
        c.setdefault("applicability", {k: little if k in small else big for k in data["classes"]})
        c.setdefault("assessment", {})
        for k in ("evidence", "test", "remediation", "ppt", "cost", "timeline", "mitre"):
            c.setdefault(k, "")
    data["meta"]["imported"] = data["meta"].get("imported") or "built in"
    return data


def load(lib: pathlib.Path | None = None, packs: pathlib.Path | None = None) -> dict | None:
    """Your imported library, plus the packs. With no library of your own, the public starter library (so the matrix always works)."""
    use_starter = lib is None and not LIB.exists()
    lib, packs = lib or LIB, packs or PACKS
    try:
        data = starter() if use_starter else json.loads(lib.read_text("utf-8"))
    except (OSError, ValueError):
        return None
    for c in data["controls"]:                                    # a library imported before the neutral names
        c["citations"] = {neutral(k): v for k, v in c.get("citations", {}).items()}
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


def base_class(data: dict) -> str:
    """The class the others are compared with: SCB/PSB in the full workbook, otherwise the library's first class."""
    return "SCB/PSB" if "SCB/PSB" in data["classes"] else data["classes"][0]


def dominance(data: dict, top: str | None = None) -> dict[str, list[str]]:
    """For each class: the controls where it is STRICTER than `top`, i.e. what complying with `top` alone would miss."""
    top = top or base_class(data)
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
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1400px;margin:0 auto;padding:14px}a{color:var(--b)}h1{font-size:1.3rem;margin:.1rem 0}h2{font-size:1rem;margin:0 0 .5rem;letter-spacing:.04em;text-transform:uppercase;color:var(--mut)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin:12px 0}
.annun{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}
.lamp{border:1px solid var(--line);border-radius:8px;padding:10px;background:var(--bg)}.lamp b{display:block;font-size:1.6rem}
.lamp.warn{border-color:var(--r);background:var(--card)}.lamp.caut{border-color:var(--a);background:var(--card)}.lamp.ok b{color:var(--g)}
.lamp.warn b{color:var(--r)}.lamp.caut b{color:var(--a)}.muted{color:var(--mut)}code{background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:0 5px}
.nav{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(76px,1fr);gap:4px;overflow-x:auto}
.col h3{font-size:.72rem;margin:0 0 4px;color:var(--mut);text-align:center;min-height:2.6em}.cell{display:block;font-size:.66rem;padding:3px 2px;margin:0 0 3px;border-radius:3px;text-align:center;color:#fff;text-decoration:none;border:1px solid transparent}
.cell.proven,.cell.met{background:#1f6f3b}.cell.partial,.cell.near{background:#7a5a12}.cell.far{background:#8e2a24}.cell.org{background:var(--u)}
.cell.na{background:var(--na);color:var(--mut)}.cell.crit{border-color:var(--ink)}.cell.should{opacity:.82}.cell.may{opacity:.6}
.legend span{display:inline-flex;align-items:center;gap:5px;margin-right:14px}.legend i{width:14px;height:14px;border-radius:3px;display:inline-block}
.two{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(min(420px,100%),1fr))}
.hm{border-collapse:collapse}.hm td,.hm th{width:58px;height:40px;text-align:center;border:1px solid var(--line);font-size:.85rem}
.bar{height:12px;border-radius:3px;background:var(--g);display:inline-block;vertical-align:middle}.bar.p{background:var(--a)}.bar.o{background:var(--u)}
table.t{border-collapse:collapse;width:100%}@media (max-width:600px){table.t{display:block;overflow-x:auto;max-width:100%}}.card{min-width:0}table.t td,table.t th{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}
.profiles a{display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;border:1px solid var(--line);border-radius:99px;text-decoration:none;font-size:.8rem}.profiles a.on{background:var(--b);color:var(--bg)}
.det{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:9;overflow:auto;padding:4vh 12px}.det:target{display:block}
.det .box{max-width:820px;margin:0 auto;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px}
.det .x{float:right;text-decoration:none}.det th{width:30%;color:var(--mut);font-weight:600}.cell:hover,.cell:focus{outline:2px solid var(--b)}
svg text{fill:var(--ink);font-size:11px}svg .ring{fill:none;stroke:var(--line)}svg .sp{stroke:var(--line)}
svg .s-t{fill:none;stroke:var(--mut);stroke-dasharray:4 3}svg .s-sx{fill:rgba(88,166,255,.25);stroke:var(--b)}svg .s-me{fill:rgba(63,185,80,.25);stroke:var(--g)}
"""
# The shared tokens and basics (doc 100); the navigator keeps only its grid colours. It used to be dark only; it now follows the device.


def _design():
    """governance/design.py, loaded by path (LESSONS: another test may own a module of the same name)."""
    spec = importlib.util.spec_from_file_location("securax_design", pathlib.Path(__file__).resolve().parent / "design.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CSS = _design().css({"--u": "#5f6b78", "--na": "#e9ecef"}, {"--u": "#3a4652", "--na": "#1a222b"}) + CSS


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


IMPACT_BY_TIER = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2}
LIKELIHOOD_BY_STATE = {"met": 1, "proven": 1, "near": 3, "partial": 3, "far": 4, "org": 4}


def risk_score(c: dict, cls: str, sx: dict) -> tuple[int, int, str] | None:
    """(likelihood, impact, source) for one applicable control: your own score wins; otherwise SecuRAX estimates it
    (ISO 31000 / NIST SP 800-30 style). Impact comes from the control's tier. Likelihood comes from the evidence: proven or at target 1,
    partly 3, not evidenced 4 (an unproven safeguard is treated as likely to fail, the cautious reading)."""
    if level(c, cls) == "N/A":
        return None
    a = c.get("assessment") or {}
    if a.get("likelihood") and a.get("impact"):
        return int(a["likelihood"]), int(a["impact"]), "you"
    return LIKELIHOOD_BY_STATE.get(state(c, sx), 4), IMPACT_BY_TIER.get(c["tier"], 3), "estimate"


def _open(r: dict) -> bool:
    return not (r.get("done") or re.search(r"closed|completed|done|resolved", r.get("status") or "", re.I))


def heatmap(data: dict, cls: str, risks: list | None = None, sx: dict | None = None) -> str:
    cells = [[[] for _ in range(5)] for _ in range(5)]
    n = {"you": 0, "estimate": 0, "register": 0}
    for c in data["controls"]:
        rs = risk_score(c, cls, sx or {})
        if rs:
            li, im, src = rs
            cells[5 - im][li - 1].append(c["id"])
            n[src] += 1
    for r in risks or []:                                      # open risks from the private register, plotted alongside
        li, im = r.get("likelihood"), r.get("impact")
        if li and im and 1 <= li <= 5 and 1 <= im <= 5 and _open(r):
            cells[5 - int(round(im))][int(round(li)) - 1].append(str(r.get("id") or "risk"))
            n["register"] += 1
    if not sum(n.values()):
        return "<p class='muted'>Nothing applies to this profile.</p>"
    h = ["<table class='hm'><tr><th>Impact ↓ / Likelihood →</th>" + "".join(f"<th>{i}</th>" for i in range(1, 6)) + "</tr>"]
    for ri, row in enumerate(cells):
        imp = 5 - ri
        tds = []
        for li, ids in enumerate(row, 1):
            s = imp * li
            col = "#8e2a24" if s >= 20 else "#7a3a12" if s >= 12 else "#7a5a12" if s >= 6 else "#1f6f3b"
            tip = f"Likelihood {li} × impact {imp} = {s}: " + ", ".join(ids[:25]) + (" …" if len(ids) > 25 else "") if ids else ""
            tds.append(f"<td style='background:{col};color:#fff' title='{E(tip)}'>{len(ids) or ''}</td>")   # white on the heat colour, in both themes
        h.append(f"<tr><th>{imp}</th>{''.join(tds)}</tr>")
    src = []
    if n["you"]:
        src.append(f"{n['you']} controls you scored")
    if n["estimate"]:
        src.append(f"{n['estimate']} estimated by SecuRAX")
    if n["register"]:
        src.append(f"{n['register']} open risks in your risk register (./securax risks list --open)")
    return ("".join(h) + f"</table><p class='muted'>Plotted: {E('; '.join(src))}. Hover a square for the controls in it. "
            "Score = likelihood × impact: 20–25 critical (act within 30 days), 12–19 high (90 days), 6–11 medium, 1–5 low.</p>"
            "<p class='muted'><b>How SecuRAX estimates:</b> impact from the control's tier (Critical 5, High 4, Medium 3, Low 2); likelihood from the evidence "
            "(proven or at your target 1, partly 3, not evidenced 4). " + (
            "<b>Your own scores:</b> the built-in starter library has none, so every square is SecuRAX's estimate. That is enough to start." if data["meta"].get("starter") else
            "<b>To set your own:</b> fill the yellow <b>Likelihood</b> and <b>Impact</b> cells in the workbook, save it in Downloads, then run "
            "<code>./securax go</code> (or <code>./securax controls import</code>): it finds and imports it. Your score always replaces the estimate.") + "</p>")


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


STATUS_TEXT = {
    "met": "At your target: your own score meets the target you set.",
    "near": "One level short of the target you set.",
    "far": "Two or more levels short of the target you set.",
    "proven": "SecuRAX proves this with evidence (a test or a journey that runs on every change).",
    "partial": "SecuRAX covers part of this; the rest is for the organisation to do and show.",
    "org": "SecuRAX cannot prove this one: it is a people, process or contract duty. Score it yourself in the workbook.",
    "na": "Does not apply to this profile.",
}


def detail(c: dict, cls: str, sx: dict, lv: str, st: str) -> str:
    """One control's panel, opened by clicking its grid cell (CSS :target, no script)."""
    a, ev = c.get("assessment") or {}, sx.get(c["id"], {})
    rs = risk_score(c, cls, sx)
    rows = [("Status", STATUS_TEXT.get(st, st)),
            ("Requirement", f"{lv} for {cls} (MUST = mandatory, SHOULD = expected unless justified, MAY = optional)"),
            ("Tier", f"{c['tier']}" + (" (white edge in the grid)" if c["tier"] == "Critical" else "")),
            ("What it asks", c.get("description")),
            ("SecuRAX evidence", (ev.get("note") or "") + ("" if not ev.get("evidence") else " · " + ", ".join(ev["evidence"]))),
            ("Evidence an auditor expects", c.get("evidence")), ("How to test", c.get("test")), ("How to fix", c.get("remediation")),
            ("Owner", c.get("owner")), ("Cost · timeline", " · ".join(x for x in (c.get("cost"), c.get("timeline")) if x)),
            ("Your scores", "" if a.get("current") is None else f"current {a['current']} / target {a.get('target')}"),
            ("Risk", "" if not rs else f"likelihood {rs[0]} × impact {rs[1]} = {rs[0] * rs[1]} ({'your score' if rs[2] == 'you' else 'estimated by SecuRAX'})"),
            ("MITRE ATT&CK", c.get("mitre"))]
    rows += [(k, v) for k, v in (c.get("citations") or {}).items()]
    rows += [(k, v) for k, v in (c.get("frameworks") or {}).items()]
    body = "".join(f"<tr><th>{E(k)}</th><td>{E(str(v))}</td></tr>" for k, v in rows if v)
    return (f"<div class='det' id='c-{E(c['id'])}'><div class='box'><a class='x' href='#grid'>Close ✕</a>"
            f"<h2>{E(c['id'])} · {E(DOMAINS.get(c['domain'], c['domain']))}</h2><h1>{E(c['title'])}</h1><table class='t'>{body}</table></div></div>")


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
    top = base_class(data)
    misses = [] if cls == CEILING else dom.get(cls, []) if cls != top else []
    stamp = dt.datetime.now().strftime("%d %b %Y %H:%M")
    h = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>"
         f"<title>Control navigator · {E(cls)}</title><style>{CSS}</style></head><body><main>"]
    h.append(f"<div class='muted'>SecuRAX control navigator · {E(data['meta'].get('version') or data['meta']['source'])} · {'built in' if data['meta'].get('starter') else 'imported ' + E(data['meta']['imported'])} · "
             f"page {E(stamp)} · <a href='/portal/cockpit.html'>Cockpit</a> · <a href='/hub.html'>All apps</a></div>")
    h.append(f"<h1>{E(cls)}: {len(app)} controls apply, {len(must)} of them MUST</h1>")
    if data["meta"].get("starter"):
        h.append("<div class='card'><b>This is the built-in starter library</b> (public, written in plain words, regulators cited by name only). "
                 "It works with no file from you. If your organisation has its own gap-assessment workbook, save it in Downloads and run "
                 "<code>./securax go</code>: it replaces this one automatically and stays private on your machine.</div>")
    # Master caution / warning panel: lamps light only when something is abnormal (the dark-cockpit rule).
    lamps = [("warn" if crit_open else "ok", len(crit_open), "Critical MUST controls not proven or at target"),
             ("caut" if gaps else "ok", len(gaps), "Vital few to close next (below)"),
             ("ok" if proven else "caut", proven, f"Proven or at target (of {len(app)})"),
             ("caut" if not scored else "ok", scored, "Controls you have scored"),
             ("warn" if misses else "ok", len(misses), f"Stricter here than {top}" if cls != CEILING else "Ceiling: covers every class"),
             ("warn" if late else "ok", len(late), "Risk treatments overdue (./securax risks overdue)")]
    h.append("<div class='card'><h2>Master caution</h2><div class='annun'>" + "".join(
        f"<div class='lamp {k}'><b>{v}</b>{E(t)}</div>" for k, v, t in lamps) + "</div></div>")
    profiles = [CEILING] + data["classes"]
    h.append("<div class='card'><h2>Profile</h2><div class='profiles'>" + "".join(
        f"<a class='{'on' if p == cls else ''}' href='/portal/navigator/{slug(p)}.html'>{E(p)}</a>" for p in profiles) + "</div>"
        "<p class='muted'>The <b>ceiling</b> takes the strictest requirement for each control across all classes, so meeting it meets every class. "
        f"{E(top)} alone is not enough for every class: see the exceptions table below.</p></div>")
    if gaps:
        h.append("<div class='card'><h2>The vital few (80/20)</h2><table class='t'><tr><th>Control</th><th>Tier</th><th>Why it matters</th><th>Owner</th></tr>" + "".join(
            f"<tr><td><b>{E(c['id'])}</b> {E(c['title'])}</td><td>{E(c['tier'])}</td><td class='muted'>{E(str(c.get('remediation') or c.get('description'))[:160])}</td><td>{E(c.get('owner') or '')}</td></tr>"
            for c in gaps) + "</table></div>")
    # MITRE-style navigator grid: one column per domain, one cell per control.
    cols, panels = [], []
    for d, name in DOMAINS.items():
        cs = [c for c in data["controls"] if c["domain"] == d]
        if not cs:
            continue
        cells = []
        for c in cs:
            lv = level(c, cls)
            st = "na" if lv == "N/A" else state(c, sx)
            cl = f"cell {st}" + (" crit" if c["tier"] == "Critical" else "") + (" should" if lv == "SHOULD" else " may" if lv == "MAY" else "")
            cells.append(f"<a class='{cl}' href='#c-{E(c['id'])}' title='{E(c['id'] + ' ' + c['title'])}'>{E(c['id'])}</a>")
            panels.append(detail(c, cls, sx, lv, st))
        cols.append(f"<div class='col'><h3>{E(name)}<br>{E(d)}</h3>{''.join(cells)}</div>")
    h.append("<div class='card'><h2>Navigator</h2><div class='legend muted'>"
             "<span><i style='background:#1f6f3b'></i>proven by SecuRAX / at your target</span><span><i style='background:#7a5a12'></i>partly / 1 level short</span>"
             "<span><i style='background:#8e2a24'></i>2+ levels short</span><span><i style='background:var(--u)'></i>the organisation's (people, process, contracts)</span>"
             "<span><i style='background:var(--na)'></i>not applicable</span><span><i style='background:var(--u);border:1px solid #fff'></i>white edge = Critical</span>"
             "<span>faded = SHOULD / MAY</span></div><p class='muted'>Each column is a domain; each box is one control, labelled with its ID. "
             "<b>Click a box</b> to see what the control asks, whether SecuRAX proves it, how to test and fix it, and the regulations behind it.</p>"
             f"<div class='nav' id='grid'>{''.join(cols)}</div></div>{''.join(panels)}")
    rows = domain_scores(data, cls, sx)
    mine = any(r["me"] is not None for r in rows)
    h.append("<div class='two'><div class='card'><h2>Maturity by domain</h2>"
             "<p class='muted'>How mature each area is, on a 0–5 scale: the centre is 0 (nothing in place), the outer ring is 5 (fully in place and proven). "
             "The further out a line reaches, the better.</p><div class='legend muted'>"
             "<span><i style='border:1px dashed var(--mut)'></i>where you aim to be (3 unless you set targets)</span>"
             "<span><i style='background:rgba(88,166,255,.5)'></i>what SecuRAX can prove with evidence today</span>"
             "<span><i style='background:rgba(63,185,80,.5)'></i>your own scores" + ("" if mine else " (appears once you score controls in the workbook)") + "</span></div>"
             f"{radar(rows)}<table class='t'><tr><th>Domain</th><th>Controls</th><th>Aim</th><th>SecuRAX proves</th><th>Your score</th></tr>"
             + "".join(f"<tr><td><b>{E(r['code'])}</b> {E(r['name'])}</td><td>{r['n']}</td><td>{r['target']}</td><td>{r['sx']}</td>"
                       f"<td>{'' if r['me'] is None else r['me']}</td></tr>" for r in rows) + f"</table></div><div class='card'><h2>Risk heat map (5 × 5)</h2>{heatmap(data, cls, risks, sx)}</div></div>")
    h.append(f"<div class='card'><h2>Regulators</h2>{regulator_bars(data, cls, sx)}</div>")
    exc = {k: v for k, v in dom.items() if v}
    h.append(f"<div class='card'><h2>Does complying with {E(top)} cover the others?</h2>"
             + (f"<p>For these classes, {E(top)} compliance alone leaves controls uncovered (they are stricter there):</p><table class='t'>"
                + "".join(f"<tr><td>{E(k)}</td><td>{', '.join(E(i) for i in v)}</td></tr>" for k, v in exc.items()) + "</table>"
                if exc else f"<p>Yes: no class is stricter than {E(top)} on any control.</p>")
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
        raise SystemExit("The control library could not be read. Run  ./securax doctor  (the built-in starter library ships with SecuRAX).")
    return data


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "help"
    if cmd in ("import", "auto"):
        # No path, a placeholder like FILE.xlsx, a folder, or a file that is not the workbook: find the workbook instead of failing.
        args = [a for a in argv[1:] if a not in ("--yes", "-y")]
        yes = cmd == "auto" or len(args) < len(argv) - 1
        path, found = (pathlib.Path(" ".join(args)).expanduser() if args else None), []
        if path and path.is_file() and not is_library_workbook(path):
            print(f"{path.name} is not the control-library workbook (it has no 'Master Catalogue' sheet). Looking for the right one…")
            path = None
        elif path and not path.is_file():
            if not path.is_dir():
                print(f"No file at {path}. Looking in Downloads, Documents, Desktop and vault/inbox instead…")
            found = [f for f in find_xlsx([path] if path.is_dir() else None) if is_library_workbook(f)]
            path = None
        if path is None:
            found = found or [f for f in find_xlsx() if is_library_workbook(f)]
            if cmd == "auto":                                   # ./securax go: import only a workbook newer than the library
                if not found or (LIB.exists() and found[0].stat().st_mtime <= LIB.stat().st_mtime):
                    write_navigator(load())                 # always a matrix: your library, or the built-in starter library
                    print("library current" if LIB.exists() else "using the built-in starter library (no workbook of your own: that is fine)")
                    return 0
                got = found[:1]
            else:
                got = found[:1] if (yes and found) else confirm(found[:1], "control-library workbook")
            if not got:
                return 1
            path = got[0]
        data = import_workbook(path)
        LIB.parent.mkdir(parents=True, exist_ok=True)
        LIB.write_text(json.dumps(data, indent=1, ensure_ascii=False), "utf-8")
        try:
            LIB.chmod(0o600)
        except OSError:
            pass
        scored = sum(1 for c in data["controls"] if c["assessment"].get("current") is not None)
        print(f"✔ {data['meta']['controls']} controls, {len(data['classes'])} classes imported into {LIB.relative_to(ROOT)} (private; {scored} scored)")
        for p in write_navigator(load())[:1]:
            print(f"✔ navigator: {p.relative_to(ROOT)}  ({_addr().web_url('hub', 8088, '/portal/navigator.html')})")
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
        data = _need()
        top = base_class(data)
        for cls, ids in dominance(data).items():
            print(f"{'✔' if not ids else '✗'} {cls:<16} " + (f"covered by {top}" if not ids else f"stricter than {top} on " + ", ".join(ids)))
        print("The ceiling profile (./securax controls profile) covers every class.")
        return 0
    if cmd == "navigator":
        ps = write_navigator(_need())
        print(f"✔ wrote {len(ps)} pages; open {_addr().web_url('hub', 8088, '/portal/navigator.html')}")
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
