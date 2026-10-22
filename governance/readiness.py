#!/usr/bin/env python3
"""Readiness for any regulation SecuRAX maps, for one organisation, by that organisation (doc 106).

    ./securax readiness demo                         a sample NBFC with fake marks: see the whole workflow in two minutes
    ./securax readiness start "NAME" --layer IV      the RBI NBFC cyber directions 2026: III (base layer under ₹500 cr, CICs),
                                                     IV (base layer ₹500 cr and above), V (middle layer and above)
    ./securax readiness start "NAME" --map cscrf --category small
                                                     any other map: cscrf (SEBI, by category mii|qre|mid|small|self),
                                                     caf (UK NCSC CAF 4), nist-ai-600-1, mit-ai-risk, pqc, owasp-ai (OWASP LLM and Agentic), free-ai (RBI FREE-AI)
    ./securax readiness [NAME]                       where it stands: the score, the vital few gaps, what is overdue
    ./securax readiness mark NAME ID STATUS [--evidence "..."] [--owner WHO] [--due YYYY-MM-DD]
                                                     STATUS is met | partly | gap | na; ID as listed (for example 121-124)
    ./securax readiness done NAME CADENCE YYYY-MM-DD the date a recurring duty was last done (va, pt, is-audit, ...)
    ./securax readiness report [NAME]                the board pack (HTML) and the auditor's sheet (CSV), both private
    ./securax readiness list                         every assessment on this machine (an auditor keeps one per client)

The requirements are the paragraph-level maps SecuRAX keeps (governance/regmap-*.json, the same ones ./securax comply reads),
paraphrased, each with the chapters or categories it applies to. Recurring duties are tracked where the text sets them (RBI). Nothing is assumed: an item nobody has assessed is "not assessed", never "met", and the
report says so. Every mark keeps who made it, when, and the evidence named. Assessments stay in vault/readiness/ (readable by
you only, never committed). Standard library only; no network.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import getpass
import html
import io
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAPS = {"rbi": "regmap-rbi-nbfc.json", "cscrf": "regmap-sebi-cscrf.json", "caf": "regmap-uk-caf-4.json",
        "nist-ai-600-1": "regmap-nist-ai-600-1.json", "mit-ai-risk": "regmap-mit-ai-risk.json", "pqc": "regmap-pqc.json",
        "owasp-ai": "regmap-owasp-llm-agentic.json", "free-ai": "regmap-rbi-free-ai.json"}
ALL = "all"                                        # the category of a map that is not split into categories
STORE = ROOT / "vault" / "readiness"
STATUSES = ("met", "partly", "gap", "na")
WORD = {"met": "Met", "partly": "Partly met", "gap": "Gap", "na": "Not applicable", "unknown": "Not assessed"}
# The duties a regulator or auditor asks about first: a gap here outranks others (weight 3). Ids from the map.
CRITICAL_RBI = {"6", "7-9", "81-82", "115-116", "28, 141", "121-124", "23, 125-126", "25-27", "47-58, 149-154",
            "8(8), 59, 127", "59(4), 129-132", "128, 133-135", "21(8), 109-110"}
# Recurring duties: (key, what, every N days, layers, the map item it evidences, basis). Paraphrased; check the Directions.
CADENCES = [
    ("board-policy", "Board reviews the technology and cybersecurity policies", 365, ("III", "IV", "V"), "6", "para 6: at least annually"),
    ("backup-test", "Backups restored in a test", 182, ("III",), "7-9", "paras 7-9 say periodic; six months is SecuRAX's default"),
    ("va", "Vulnerability assessment of critical and internet-facing systems", 182, ("IV", "V"), "121-124", "paras 121-124: every six months"),
    ("pt", "Penetration test of critical and internet-facing systems", 365, ("IV", "V"), "121-124", "paras 121-124: every 12 months"),
    ("it-risk", "IT risk assessment brought to the Board", 365, ("IV", "V"), "32, 96, 98", "paras 32, 96, 98: annual"),
    ("is-audit", "Information systems audit", 365, ("IV", "V"), "47-58, 149-154", "paras 47-58: annual"),
    ("bcp-test", "BCP and DR test with a worst-case scenario", 365, ("IV",), "59(4), 129-132", "para 59(4): at least annually"),
    ("bcp-test-critical", "BCP and DR test of critical systems", 182, ("V",), "59(4), 129-132", "paras 129-132: half-yearly for critical systems"),
    ("ciso-board", "CISO reviews the cyber posture with the Board", 91, ("V",), "81-82", "paras 81-82: quarterly"),
]
SOON = 30                                          # days before a recurring duty that it shows as "due soon"


def today() -> dt.date:
    return dt.date.fromisoformat(os.environ["SECURAX_TODAY"]) if os.environ.get("SECURAX_TODAY") else dt.date.today()


CRITICAL = {"rbi": CRITICAL_RBI}                    # per map; a map with none ranks every gap the same


def regmap(key: str = "rbi") -> dict:
    if key not in MAPS:
        raise ValueError(f"map must be one of {', '.join(MAPS)}")
    return json.loads((ROOT / "governance" / MAPS[key]).read_text("utf-8"))


def categories(key: str = "rbi") -> dict:
    """{category: what it means}; a map that is not split has the one category 'all'."""
    return regmap(key).get("categories") or {ALL: "all requirements"}


def requirements(layer: str, key: str = "rbi") -> list[dict]:
    """The map's items that apply to this chapter or category, in the map's order."""
    out = []
    for i in regmap(key)["items"]:
        ap = i.get("applies")
        if ap == "all" or layer == ALL or (isinstance(ap, list) and layer in ap):
            out.append(i)
    return out


def _key(a: dict) -> str:
    return a.get("map", "rbi")


def _where(a: dict) -> str:
    k, layer = _key(a), a["layer"]
    cats = categories(k)
    if k == "rbi":
        return cats[layer]                         # the map names it in full: "Chapter V — NBFC Middle, ..."
    return "all requirements" if layer == ALL else f"category {layer} ({cats.get(layer, layer)})"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:60] or "assessment"


def _private(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def load(name: str, store: pathlib.Path | None = None) -> dict:
    store = store or STORE
    p = store / f"{slug(name)}.json"
    if not p.exists():
        raise KeyError(name)
    return json.loads(p.read_text("utf-8"))


def save(a: dict, store: pathlib.Path | None = None) -> pathlib.Path:
    store = store or STORE
    p = store / f"{slug(a['entity'])}.json"
    _private(p, json.dumps(a, ensure_ascii=False, indent=1))
    return p


def start(name: str, layer: str, store: pathlib.Path | None = None, demo: bool = False, key: str = "rbi") -> dict:
    store = store or STORE
    cats = categories(key)
    if layer not in cats:
        raise ValueError(("layer" if key == "rbi" else "category") + f" must be one of {', '.join(cats)}")
    if (store / f"{slug(name)}.json").exists():
        raise FileExistsError(name)
    a = {"entity": name, "map": key, "layer": layer, "created": today().isoformat(), "demo": demo, "marks": {}, "done": {}}
    save(a, store)
    return a


def mark(a: dict, rid: str, status: str, evidence: str = "", owner: str = "", due: str = "", by: str = "") -> dict:
    ids = {i["id"] for i in requirements(a["layer"], _key(a))}
    if rid not in ids:
        raise KeyError(rid)
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    if due:
        dt.date.fromisoformat(due)
    if status == "met" and not evidence.strip():
        raise ValueError("a 'met' needs the evidence that proves it (--evidence \"...\"): an auditor will ask for it")
    a["marks"][rid] = {"status": status, "evidence": evidence.strip(), "owner": owner.strip(), "due": due,
                       "by": by or getpass.getuser(), "at": dt.datetime.now().isoformat(timespec="seconds")}
    return a


def cadences(a: dict, now: dt.date | None = None) -> list[dict]:
    now = now or today()
    out = []
    for key, what, every, layers, item, basis in (CADENCES if _key(a) == "rbi" else []):
        if a["layer"] not in layers:
            continue
        last = a["done"].get(key)
        nxt = (dt.date.fromisoformat(last) + dt.timedelta(days=every)) if last else None
        state = "never" if not last else "overdue" if nxt < now else "soon" if (nxt - now).days <= SOON else "ok"
        out.append({"key": key, "what": what, "every_days": every, "last": last or "", "next": nxt.isoformat() if nxt else "",
                    "state": state, "item": item, "basis": basis})
    return out


def _weight(i: dict, st: str, m: dict, now: dt.date, crit: set) -> float:
    w = (3 if i["id"] in crit else 1) * {"gap": 3, "unknown": 2, "partly": 1}.get(st, 0)
    if m.get("due") and m["due"] < now.isoformat():
        w *= 1.5
    return w


def summary(a: dict, now: dt.date | None = None) -> dict:
    now = now or today()
    reqs = requirements(a["layer"], _key(a))
    crit = CRITICAL.get(_key(a), set())
    rows, counts = [], {k: 0 for k in (*STATUSES, "unknown")}
    for i in reqs:
        m = a["marks"].get(i["id"], {})
        st = m.get("status", "unknown")
        counts[st] += 1
        helps = [e[4:] for e in i.get("evidence", []) if e.startswith("cmd:")] if i.get("status") in ("supported", "partial") else []
        rows.append({"id": i["id"], "title": i["title"], "status": st, "critical": i["id"] in crit, "mark": m,
                     "helps": helps, "weight": _weight(i, st, m, now, crit)})
    scope = len(reqs) - counts["na"]
    score = round(100 * (counts["met"] + 0.5 * counts["partly"]) / scope) if scope else 0
    assessed = round(100 * (scope - counts["unknown"]) / scope) if scope else 0
    vital = sorted((r for r in rows if r["weight"]), key=lambda r: (-r["weight"], r["id"]))[:5]
    cad = cadences(a, now)
    return {"entity": a["entity"], "layer": a["layer"], "map": _key(a), "where": _where(a), "title": regmap(_key(a))["source"]["title"], "demo": a.get("demo", False), "score": score, "assessed_pct": assessed,
            "counts": counts, "in_scope": scope, "vital": vital, "rows": rows, "cadences": cad,
            "overdue": [c for c in cad if c["state"] in ("overdue", "never")],
            "late_actions": [r for r in rows if r["mark"].get("due") and r["mark"]["due"] < now.isoformat() and r["status"] != "met"]}


# -- the board pack and the auditor's sheet ----------------------------------------------------------------------------------

_CSS = """:root{--bg:#f5f5f7;--card:#ffffff;--ink:#1d1d1f;--mut:#57606a;--line:#d2d2d7;--accent:#0a5bd8;--red:#b42318;--amber:#8a5a00;--green:#1f7a3a}
@media (prefers-color-scheme:dark){:root{--bg:#0b0f14;--card:#151b23;--ink:#f0f3f6;--mut:#9ba7b4;--line:#2a333d;--accent:#6ea8ff;--red:#ff7b72;--amber:#e3b341;--green:#56d364}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:960px;margin:0 auto;padding:24px 16px}h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:28px 0 8px}
.mut{color:var(--mut)}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:12px 0;overflow-x:auto}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}.kpi b{display:block;font-size:28px}
table{width:100%;min-width:600px;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:top}
.s-met{color:var(--green)}.s-gap,.s-overdue,.s-never{color:var(--red)}.s-partly,.s-unknown,.s-soon{color:var(--amber)}
.banner{border-left:4px solid var(--amber);padding:8px 12px;background:var(--card)}@media print{body{background:#fff}}"""


def _e(s) -> str:
    return html.escape(str(s))


def board_html(s: dict, now: dt.date | None = None) -> str:
    now = now or today()
    c = s["counts"]
    demo = ('<p class="banner"><b>Sample data.</b> This NBFC and every mark in it are invented, to show the workflow.</p>'
            if s["demo"] else "")
    vital = "".join(f"<tr><td>{_e(r['id'])}</td><td>{_e(r['title'])}</td><td class='s-{r['status']}'>{_e(WORD[r['status']])}</td>"
                    f"<td>{_e(r['mark'].get('owner') or 'no owner')}</td><td>{_e(r['mark'].get('due') or 'no date')}</td></tr>"
                    for r in s["vital"]) or "<tr><td colspan=5>No open gaps among the assessed items.</td></tr>"
    cad = "".join(f"<tr><td>{_e(x['what'])}</td><td>{_e(x['last'] or 'no record')}</td><td>{_e(x['next'] or 'now')}</td>"
                  f"<td class='s-{x['state']}'>{_e({'never': 'No record', 'overdue': 'Overdue', 'soon': 'Due soon', 'ok': 'On time'}[x['state']])}</td>"
                  f"<td class='mut'>{_e(x['basis'])}</td></tr>" for x in s["cadences"])
    allrows = "".join(f"<tr><td>{_e(r['id'])}</td><td>{_e(r['title'])}</td><td class='s-{r['status']}'>{_e(WORD[r['status']])}</td>"
                      f"<td>{_e(r['mark'].get('evidence') or ('none recorded' if r['status'] != 'unknown' else ''))}"
                      + (f"<div class='mut'>by {_e(r['mark']['by'])}, {_e(r['mark']['at'][:10])}</div>" if r["mark"] else "")
                      + (f"<div class='mut'>SecuRAX can produce evidence: ./securax {_e(', ./securax '.join(r['helps']))}</div>" if r["helps"] else "")
                      + "</td></tr>" for r in s["rows"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Readiness</title><style>{_CSS}</style></head><body><main>
<h1>Readiness: {_e(s['title'])}</h1>
<p class="mut">{_e(s['entity'])} · {_e(s['where'])} · as at {now.isoformat()}</p>{demo}
<div class="kpis"><div class="card kpi"><b>{s['score']}%</b>readiness of what is in scope</div>
<div class="card kpi"><b>{s['assessed_pct']}%</b>of items assessed so far</div>
<div class="card kpi"><b class="s-gap">{c['gap']}</b>gaps</div>
<div class="card kpi"><b class="s-overdue">{len(s['overdue'])}</b>recurring duties overdue or never recorded</div></div>
<p class="mut">Readiness counts Met as 1 and Partly met as half, over the {s['in_scope']} items in scope. {c['unknown']} item(s) are not assessed:
no claim is made about them, and they do not count as met.</p>
<h2>The vital few: decide these first</h2><div class="card"><table><tr><th>Ref</th><th>Requirement</th><th>Status</th><th>Owner</th><th>Due</th></tr>{vital}</table></div>
{'<h2>Recurring duties</h2><div class="card"><table><tr><th>Duty</th><th>Last done</th><th>Next due</th><th>State</th><th>Basis</th></tr>' + cad + '</table></div>' if s['cadences'] else ''}
<h2>Every requirement, with its evidence</h2><div class="card"><table><tr><th>Ref</th><th>Requirement</th><th>Status</th><th>Evidence and provenance</th></tr>{allrows}</table></div>
<p class="mut">Requirements are paraphrased from the source ({_e(s['title'])}); read the source for the exact text.
This is a self-assessment by the entity, not an audit opinion. Made with SecuRAX readiness.</p>
</main></body></html>"""


def auditor_csv(s: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["para", "requirement", "status", "critical", "evidence", "owner", "due", "marked_by", "marked_at"])
    for r in s["rows"]:
        m = r["mark"]
        w.writerow([r["id"], r["title"], WORD[r["status"]], "yes" if r["critical"] else "", m.get("evidence", ""), m.get("owner", ""),
                    m.get("due", ""), m.get("by", ""), m.get("at", "")])
    return buf.getvalue()


def report(a: dict, store: pathlib.Path | None = None) -> tuple[pathlib.Path, pathlib.Path]:
    store = store or STORE
    s = summary(a)
    base = store / slug(a["entity"])
    hp, cp = base.with_name(base.name + "-board.html"), base.with_name(base.name + "-auditor.csv")
    _private(hp, board_html(s))
    _private(cp, auditor_csv(s))
    return hp, cp


# -- the sample ----------------------------------------------------------------------------------------------------------------

DEMO_NAME = "Sample NBFC (fake)"
_DEMO_MARKS = [
    ("6", "met", "Board minutes approving the policy, item 4 (sample)", "Company Secretary", ""),
    ("81-82", "partly", "CISO appointed; reports to the Head of IT today (sample)", "MD", "+30"),
    ("115-116", "gap", "", "Head of IT", "+45"),
    ("28, 141", "partly", "Escalation matrix drafted; no 6-hour drill yet (sample)", "CISO", "+21"),
    ("121-124", "met", "VA report dated four months ago (sample)", "CISO", ""),
    ("47-58, 149-154", "gap", "", "Audit Committee", "+60"),
    ("33-34", "na", "", "", ""),
]


def demo(store: pathlib.Path | None = None) -> dict:
    store = store or STORE
    p = store / f"{slug(DEMO_NAME)}.json"
    if p.exists():
        p.unlink()
    a = start(DEMO_NAME, "V", store, demo=True)
    now = today()
    for rid, st, ev, owner, due in _DEMO_MARKS:
        mark(a, rid, st, ev, owner, (now + dt.timedelta(days=int(due))).isoformat() if due else "", by="sample")
    a["done"] = {"va": (now - dt.timedelta(days=120)).isoformat(), "pt": (now - dt.timedelta(days=400)).isoformat(),
                 "ciso-board": (now - dt.timedelta(days=80)).isoformat()}
    save(a, store)
    return a


# -- the command ---------------------------------------------------------------------------------------------------------------

def _all(store: pathlib.Path | None = None) -> list[dict]:
    store = store or STORE
    return [json.loads(p.read_text("utf-8")) for p in sorted(store.glob("*.json"))] if store.is_dir() else []


def _pick(name: str | None, store: pathlib.Path | None = None) -> dict:
    store = store or STORE
    if name:
        return load(name, store)
    real = [a for a in _all(store) if not a.get("demo")] or _all(store)
    if not real:
        raise LookupError("none")
    return max(real, key=lambda a: a.get("created", ""))


def _print(s: dict) -> None:
    c = s["counts"]
    print(f"{s['entity']} · {s['title'][:60]} · {s['where']}" + ("  [sample data]" if s["demo"] else ""))
    print(f"  readiness {s['score']}% of {s['in_scope']} items in scope · {s['assessed_pct']}% assessed"
          f" · met {c['met']}, partly {c['partly']}, gap {c['gap']}, not assessed {c['unknown']}, n/a {c['na']}")
    print("  the vital few:")
    for r in s["vital"]:
        m = r["mark"]
        print(f"    {'★' if r['critical'] else ' '} {r['id']:<16} {WORD[r['status']]:<13} {r['title'][:70]}"
              + (f"  (owner {m['owner']}" + (f", due {m['due']}" if m.get("due") else "") + ")" if m.get("owner") else ""))
    for x in s["overdue"]:
        print(f"  ⚠ {x['what']}: " + ("no record of it being done" if x["state"] == "never" else f"overdue since {x['next']}"))
    nxt = s["vital"][0] if s["vital"] else None
    if nxt:
        print(f"Next: ./securax readiness mark \"{s['entity']}\" \"{nxt['id']}\" met --evidence \"what proves it\"   (or partly | gap | na)")
    print(f"Board pack: ./securax readiness report \"{s['entity']}\"")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] in (["-h"], ["--help"], ["help"]):
        print(__doc__)
        return 0
    cmd = argv[0] if argv and argv[0] in ("demo", "start", "mark", "done", "report", "list") else "show"
    rest = argv[1:] if cmd != "show" else argv
    try:
        if cmd == "demo":
            a = demo()
            _print(summary(a))
            hp, cp = report(a)
            print(f"Sample board pack: {hp}\nAuditor's sheet: {cp}\nStart your own: ./securax readiness start \"Your NBFC\" --layer IV")
            return 0
        if cmd == "list":
            items = _all()
            if not items:
                print("No assessments yet. See one: ./securax readiness demo   Start one: ./securax readiness start \"Your NBFC\" --layer IV")
                return 0
            for a in items:
                s = summary(a)
                print(f"  {a['entity']:<34} {_key(a):<14} {a['layer']:<5} readiness {s['score']:>3}%  assessed {s['assessed_pct']:>3}%"
                      f"  overdue {len(s['overdue'])}" + ("  [sample]" if a.get("demo") else ""))
            return 0
        if cmd == "start":
            ap = argparse.ArgumentParser(prog="securax readiness start")
            ap.add_argument("name")
            ap.add_argument("--map", default="rbi", choices=list(MAPS))
            ap.add_argument("--layer", "--category", dest="layer", default="",
                            help="RBI: III|IV|V; CSCRF: mii|qre|mid|small|self; maps without categories: leave out")
            o = ap.parse_args(rest)
            cats = categories(o.map)
            if not o.layer and list(cats) != [ALL]:
                print(("--layer" if o.map == "rbi" else "--category") + f" is needed for {o.map}: " + ", ".join(f"{k} ({v})" for k, v in cats.items()))
                return 2
            a = start(o.name, o.layer or ALL, key=o.map)
            print(f"Started: {o.name}, {_where(a)}, {len(requirements(a['layer'], o.map))} requirements, all not assessed.")
            _print(summary(a))
            return 0
        if cmd == "mark":
            ap = argparse.ArgumentParser(prog="securax readiness mark")
            ap.add_argument("name")
            ap.add_argument("id")
            ap.add_argument("status", choices=STATUSES)
            ap.add_argument("--evidence", default="")
            ap.add_argument("--owner", default="")
            ap.add_argument("--due", default="")
            o = ap.parse_args(rest)
            a = load(o.name)
            mark(a, o.id, o.status, o.evidence, o.owner, o.due)
            save(a)
            s = summary(a)
            print(f"Marked {o.id} {WORD[o.status]}. Readiness now {s['score']}%, {s['assessed_pct']}% assessed.")
            return 0
        if cmd == "done":
            if len(rest) != 3:
                print("Usage: ./securax readiness done NAME CADENCE YYYY-MM-DD   cadences: " + ", ".join(c[0] for c in CADENCES))
                return 2
            a = load(rest[0])
            keys = {c["key"] for c in cadences(a)}
            if rest[1] not in keys:
                print(f"'{rest[1]}' is not a recurring duty here: " + (", ".join(sorted(keys)) or "this map sets none"))
                return 2
            d = dt.date.fromisoformat(rest[2])
            if d > today():
                print("That date is in the future: record a duty once it is done.")
                return 2
            a["done"][rest[1]] = d.isoformat()
            save(a)
            x = [c for c in cadences(a) if c["key"] == rest[1]][0]
            print(f"Recorded. {x['what']}: next due {x['next']}.")
            return 0
        if cmd == "report":
            a = _pick(rest[0] if rest else None)
            hp, cp = report(a)
            print(f"Board pack: {hp}\nAuditor's sheet: {cp}\nBoth stay on this machine (readable by you only). Open the pack in a browser, or print it to PDF.")
            return 0
        a = _pick(rest[0] if rest else None)
        _print(summary(a))
        return 0
    except LookupError as e:
        if str(e) == "'none'" or str(e) == "none":
            print("No assessment yet. See one: ./securax readiness demo   Start yours: ./securax readiness start \"Your NBFC\" --layer IV")
            return 1
        print(f"Not found: {e}. ./securax readiness list shows the assessments; the requirement ids are in the board pack.")
        return 1
    except FileExistsError as e:
        print(f"An assessment named {e} already exists. ./securax readiness \"{e}\" shows it.")
        return 1
    except ValueError as e:
        print(str(e))
        return 2


if __name__ == "__main__":
    sys.exit(main())
