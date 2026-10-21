#!/usr/bin/env python3
"""The CISO's ready reckoner (doc 94 §8): open any capability or role in the cockpit and the answer is one click away.

    ./securax govern reckon ID            the card in the terminal (a capability id like tec-edr, or a role id like soc_l2)
    ./securax govern rfp ID [--out F.md]  an RFP pack to start from: scope, mandatory specs, sizing, evaluation, SLAs, clauses
    ./securax govern reckoner [--out DIR] write every page (the cockpit does this itself, next to portal/cockpit.html)

For each capability: what it is and protects, where it sits and how it works, the 20% that gives 80% of the value, at
least three vendors (with an Indian or open-source option where one is real), an indicative Indian cost for the reference
organisation, the RFP pack, KPIs, pitfalls and sources. For each role: the job description, must-have and good-to-have,
experience, certifications, interview tests, KPIs, the salary band and where good people come from.

The research lives in governance/reckoner/*.json (one file per layer, plus roles.json), each item with its sources and an
"as_of" month. Prices are indicative bands for India, excluding GST: get three quotes. The pages carry no script; their only
outside links are the sources. Standard library only.
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "governance" / "reckoner"
OUT = ROOT / "portal" / "reckoner"
CAP_FIELDS = ("summary", "protects", "placement", "how", "pareto", "vendors", "cost", "rfp", "kpis", "pitfalls", "sources")
ROLE_FIELDS = ("purpose", "responsibilities", "must", "good", "experience", "certs_must", "interview", "kpis", "salary", "sources")
E = html.escape

CSS = """:root{--bg:#f6f7f9;--card:#fff;--ink:#14202b;--mut:#5a6876;--line:#dde2e8;--acc:#2554c7;--g:#176f3d;--a:#8a5a00;--r:#c0392b}
@media (prefers-color-scheme:dark){:root{--bg:#0f141a;--card:#18202a;--ink:#e8edf2;--mut:#9aa7b5;--line:#2b3744;--acc:#7aa2ff;--g:#4cc884;--a:#e3a63c;--r:#ff7a6b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:16px}h1{font-size:1.45rem;margin:.3rem 0}h2{font-size:1.05rem;margin:1.2rem 0 .4rem}
a{color:var(--acc)}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:12px 0}
.muted{color:var(--mut);font-size:.9rem}.tag{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:0 9px;font-size:.8rem;margin-right:6px}
ul{margin:.3rem 0;padding-left:1.2rem}li{margin:.2rem 0}table{width:100%;border-collapse:collapse;font-size:.92rem}
th{text-align:left;border-bottom:2px solid var(--line);padding:6px}td{border-bottom:1px solid var(--line);padding:7px 6px;vertical-align:top}
.cols{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}.big{font-size:1.1rem;font-weight:650}
details summary{cursor:pointer;font-weight:600}nav{font-size:.9rem}code{background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:1px 6px}
.ask{border-left:6px solid var(--acc)}.tbl{overflow-x:auto}td,li,p,a{overflow-wrap:anywhere}"""


def _govern():
    import importlib.util
    spec = importlib.util.spec_from_file_location("securax_govern_r", ROOT / "governance" / "govern.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load(data: pathlib.Path | None = None) -> dict:
    """{"caps": {id: item}, "roles": {id: item}, "as_of": {...}} from every governance/reckoner/*.json."""
    caps, roles, as_of = {}, {}, {}
    for f in sorted((data or DATA).glob("*.json")):
        doc = json.loads(f.read_text("utf-8"))
        target = roles if f.stem == "roles" else caps
        for k, v in (doc.get("items") or {}).items():
            target[k] = v
            as_of[k] = doc.get("as_of", "")
    return {"caps": caps, "roles": roles, "as_of": as_of}


def problems(rk: dict | None = None) -> list[str]:
    """What a CISO would trip over: a capability or role with no page, a missing field, fewer than 3 vendors, no source."""
    rk = rk or load()
    g = _govern()
    cat = g.catalog()
    out = []
    for c in cat["capabilities"]:
        it = rk["caps"].get(c["id"])
        if not it:
            out.append(f"{c['id']}: no ready-reckoner entry")
            continue
        out += [f"{c['id']}: missing {f}" for f in CAP_FIELDS if not it.get(f)]
        if len(it.get("vendors") or []) < 3:
            out.append(f"{c['id']}: fewer than 3 vendors or options")
        for s in it.get("sources") or []:
            if not str(s.get("url", "")).startswith("https://"):
                out.append(f"{c['id']}: a source without an https address")
    for r in cat["roles"]:
        it = rk["roles"].get(r["id"])
        if not it:
            out.append(f"{r['id']}: no job description")
            continue
        out += [f"{r['id']}: missing {f}" for f in ROLE_FIELDS if not it.get(f)]
    out += [f"{k}: not in the catalog" for k in rk["caps"] if k not in {c["id"] for c in cat["capabilities"]}]
    out += [f"{k}: not a known role" for k in rk["roles"] if k not in {r["id"] for r in cat["roles"]}]
    return out


# ───────────────────────────────────────────── text helpers ─────────────────────────────────────────────
def _ul(items) -> str:
    items = [i for i in (items or []) if i]
    return "<ul>" + "".join(f"<li>{E(str(i))}</li>" for i in items) + "</ul>" if items else "<p class='muted'>Not recorded yet.</p>"


def _sources(items) -> str:
    rows = []
    for s in items or []:
        url = str(s.get("url", ""))
        if url.startswith("https://"):
            rows.append(f"<li><a href='{E(url)}' rel='noopener noreferrer'>{E(str(s.get('title') or url))}</a></li>")
    return "<ul>" + "".join(rows) + "</ul>" if rows else "<p class='muted'>No sources recorded.</p>"


def _page(title: str, body: str, crumbs: str) -> str:
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{E(title)} · Ready reckoner</title><style>{CSS}</style></head><body><main><nav>{crumbs}</nav>{body}"
            "<p class='muted'>Indicative, for planning. Prices are bands for India excluding GST: get three quotes. Check each source on the day.</p>"
            "</main></body></html>")


def _crumbs(back_to_cockpit: str = "../cockpit.html") -> str:
    return f"<a href='{back_to_cockpit}#govern'>← Cockpit</a> · <a href='index.html'>Ready reckoner</a>"


# ───────────────────────────────────────────── capability page ─────────────────────────────────────────────
def cap_page(c: dict, it: dict, as_of: str, marks: dict | None = None) -> str:
    g = _govern()
    st = g.state(c["id"], marks or {}) if marks is not None else ""
    cost = it.get("cost") or {}
    vend = "".join(f"<tr><td><b>{E(v.get('name', ''))}</b></td><td>{E(v.get('kind', ''))}</td><td>{E(v.get('fit', ''))}</td>"
                   f"<td>{E(v.get('india', ''))}</td></tr>" for v in it.get("vendors") or [])
    rfp = it.get("rfp") or {}
    body = (f"<h1>{E(c['name'])}</h1><p><span class='tag'>{E(c['tier'])} tier</span><span class='tag'>{E(c['area'])}</span>"
            f"<span class='tag'>owner: {E(c.get('owner', ''))}</span>" + (f"<span class='tag'>you: {E(st)}</span>" if st else "")
            + f"<span class='tag'>as of {E(as_of)}</span></p>"
            f"<div class='card ask'><p class='big'>{E(it.get('summary', ''))}</p><p><b>It protects:</b> {E(it.get('protects', ''))}</p>"
            f"<p><b>Why now:</b> {E(c.get('why', ''))}</p></div>"
            f"<div class='cols'><div class='card'><h2>Where it sits</h2><p>{E(it.get('placement', ''))}</p><p>{E(it.get('architecture', ''))}</p></div>"
            f"<div class='card'><h2>How it works</h2><p>{E(it.get('how', ''))}</p><h2>The 20% that gives 80%</h2>{_ul(it.get('pareto'))}</div></div>"
            f"<div class='card'><h2>Options in the market</h2><div class='tbl'><table><tr><th>Vendor or option</th><th>Kind</th><th>Fit</th><th>India</th></tr>{vend}</table></div></div>"
            f"<div class='card'><h2>What it costs (indicative)</h2><p class='big'>{E(cost.get('band', ''))}</p>"
            f"<p>{E(cost.get('unit', ''))}{' · ' if cost.get('unit') else ''}for the reference organisation: {E(cost.get('reference_org', ''))}</p>"
            f"<p><b>What moves the price:</b></p>{_ul(cost.get('drivers'))}<p class='muted'>{E(cost.get('note', 'indicative; get three quotes'))}</p></div>"
            f"<div class='card'><h2>Start the RFP</h2><p>The full pack as a file: <a href='rfp/{E(c['id'])}.md'>rfp/{E(c['id'])}.md</a> "
            f"(or <code>./securax govern rfp {E(c['id'])}</code>).</p>"
            f"<details open><summary>Scope of work</summary>{_ul(rfp.get('scope'))}</details>"
            f"<details><summary>Mandatory technical specifications</summary>{_ul(rfp.get('must'))}</details>"
            f"<details><summary>Desirable</summary>{_ul(rfp.get('should'))}</details>"
            f"<details><summary>Sizing to give bidders</summary>{_ul(rfp.get('sizing'))}</details>"
            f"<details><summary>Evaluation criteria</summary>{_ul(rfp.get('evaluation'))}</details>"
            f"<details><summary>Service levels</summary>{_ul(rfp.get('sla'))}</details>"
            f"<details><summary>India and BFSI clauses</summary>{_ul(rfp.get('clauses'))}</details></div>"
            f"<div class='cols'><div class='card'><h2>How you know it works</h2>{_ul(it.get('kpis'))}</div>"
            f"<div class='card'><h2>Common mistakes</h2>{_ul(it.get('pitfalls'))}</div></div>"
            f"<div class='card'><h2>Sources</h2>{_sources(it.get('sources'))}</div>")
    return _page(c["name"], body, _crumbs())


def role_page(r: dict, it: dict, as_of: str) -> str:
    body = (f"<h1>{E(r['name'])}</h1><p><span class='tag'>{E(r.get('vertical', ''))}</span><span class='tag'>reports to: {E(it.get('reports_to', ''))}</span>"
            f"<span class='tag'>as of {E(as_of)}</span></p>"
            f"<div class='card ask'><p class='big'>{E(it.get('purpose', ''))}</p><p><b>Salary (India, metro):</b> {E(it.get('salary', ''))}</p></div>"
            f"<div class='card'><h2>Job description: what they do</h2>{_ul(it.get('responsibilities'))}</div>"
            f"<div class='cols'><div class='card'><h2>Must have</h2>{_ul(it.get('must'))}<p><b>Experience:</b> {E(it.get('experience', ''))}</p>"
            f"<p><b>Education:</b> {E(it.get('education', ''))}</p><p><b>Certifications that matter:</b></p>{_ul(it.get('certs_must'))}</div>"
            f"<div class='card'><h2>Good to have</h2>{_ul(it.get('good'))}<p><b>Also worth having:</b></p>{_ul(it.get('certs_good'))}</div></div>"
            f"<div class='cols'><div class='card'><h2>How to spot the best candidate</h2>{_ul(it.get('interview'))}</div>"
            f"<div class='card'><h2>How the role is measured</h2>{_ul(it.get('kpis'))}<p><b>Where they come from, where they go:</b> {E(it.get('pipeline', ''))}</p></div></div>"
            f"<div class='card'><h2>Sources</h2>{_sources(it.get('sources'))}</div>")
    return _page(r["name"], body, _crumbs())


def _sentence(t: str) -> str:
    t = str(t or "").strip()
    return t if not t or t.endswith((".", "!", "?")) else t + "."


def _lower(t: str) -> str:
    t = _sentence(t)
    return t[:1].lower() + t[1:] if t[:2] != t[:2].upper() else t


def rfp_md(c: dict, it: dict, as_of: str, org: str = "[Organisation]") -> str:
    rfp, cost = it.get("rfp") or {}, it.get("cost") or {}

    def sec(title, items):
        items = [i for i in (items or []) if i]
        return f"## {title}\n\n" + ("\n".join(f"- {i}" for i in items) if items else "- [to be completed]") + "\n\n"
    vend = "\n".join(f"- {v.get('name')} ({v.get('kind')}): {v.get('fit')}" for v in it.get("vendors") or [])
    return (f"# Request for proposal: {c['name']}\n\n**Issued by:** {org} · **Date:** [DD Month YYYY] · **Reference:** [RFP number]\n\n"
            f"> Draft from the SecuRAX ready reckoner ({as_of}). Review every line with procurement and legal; replace each [bracket].\n\n"
            f"## 1. Background and objective\n\n{_sentence(it.get('summary', ''))} It protects {_lower(it.get('protects', ''))} {_sentence(c.get('why', ''))}\n\n"
            + sec("2. Scope of work", rfp.get("scope"))
            + sec("3. Mandatory technical specifications (a bid that misses one is not evaluated)", rfp.get("must"))
            + sec("4. Desirable specifications", rfp.get("should"))
            + sec("5. Sizing (current, and growth over 3 years)", rfp.get("sizing"))
            + f"## 6. Architecture and placement\n\n{it.get('placement', '')} {it.get('architecture', '')}\n\n"
            + sec("7. Service levels", rfp.get("sla"))
            + sec("8. Evaluation criteria", rfp.get("evaluation"))
            + sec("9. Contract clauses (India and BFSI)", rfp.get("clauses"))
            + f"## 10. Commercial format\n\n- Price per {cost.get('unit') or 'unit'} for years 1, 2 and 3, excluding GST, with licence, implementation, "
              "support and training shown separately\n- Payment linked to milestones and acceptance\n\n"
            + f"## 11. Budgetary reference (internal, remove before issue)\n\n- Indicative band: {cost.get('band', '')}\n"
              f"- For the reference organisation: {cost.get('reference_org', '')}\n- Options to invite:\n{vend}\n")


# ───────────────────────────────────────────── the pages ─────────────────────────────────────────────
def index_page(rk: dict) -> str:
    g = _govern()
    cat = g.catalog()
    rows = []
    for label, pick in g.STACK:
        caps = [c for c in cat["capabilities"] if pick(c)]
        if caps:
            rows.append(f"<h2>{E(label)}</h2><ul>" + "".join(
                f"<li><a href='{E(c['id'])}.html'>{E(c['name'])}</a> <span class='muted'>· {E(c['tier'])}</span></li>"
                for c in sorted(caps, key=lambda c: (g.TIERS.index(c["tier"]), c["name"]))) + "</ul>")
    roles = "".join(f"<li><a href='role-{E(r['id'])}.html'>{E(r['name'])}</a></li>" for r in cat["roles"])
    body = ("<h1>Ready reckoner</h1><p class='muted'>Every capability and role in the Govern catalog: what it is, what it costs, "
            "who sells it, how to buy it, and who to hire. Open one from the cockpit, or from here.</p>"
            f"<div class='cols'><div class='card'>{''.join(rows)}</div><div class='card'><h2>People</h2><ul>{roles}</ul></div></div>")
    return _page("Ready reckoner", body, "<a href='../cockpit.html#govern'>← Cockpit</a>")


def build(out: pathlib.Path | None = None, rk: dict | None = None, marks: dict | None = None) -> int:
    """Write every page and RFP pack into out (portal/reckoner/). Returns the number of pages."""
    out, rk = out or OUT, rk or load()
    g = _govern()
    cat = g.catalog()
    (out / "rfp").mkdir(parents=True, exist_ok=True)
    n = 0
    for c in cat["capabilities"]:
        it = rk["caps"].get(c["id"]) or {"summary": "Not researched yet: see the Govern catalog.", "protects": "", "vendors": []}
        (out / f"{c['id']}.html").write_text(cap_page(c, it, rk["as_of"].get(c["id"], ""), marks), "utf-8")
        (out / "rfp" / f"{c['id']}.md").write_text(rfp_md(c, it, rk["as_of"].get(c["id"], "")), "utf-8")
        n += 1
    for r in cat["roles"]:
        it = rk["roles"].get(r["id"]) or {"purpose": "Not researched yet.", "responsibilities": [r.get("skills", "")], "certs_must": [r.get("certs", "")]}
        (out / f"role-{r['id']}.html").write_text(role_page(r, it, rk["as_of"].get(r["id"], "")), "utf-8")
        n += 1
    (out / "index.html").write_text(index_page(rk), "utf-8")
    return n + 1


def card_text(key: str, rk: dict | None = None) -> str:
    """The terminal version: enough to answer a question in a meeting."""
    rk = rk or load()
    cat = _govern().catalog()
    c = next((c for c in cat["capabilities"] if c["id"] == key), None)
    if c:
        it, cost = rk["caps"].get(key) or {}, (rk["caps"].get(key) or {}).get("cost") or {}
        lines = [f"{c['name']}  ({c['tier']} tier, {c['area']})", "", it.get("summary", ""), f"Protects: {it.get('protects', '')}",
                 f"Where: {it.get('placement', '')}", f"Cost: {cost.get('band', '')} ({cost.get('reference_org', '')})", "", "Options:"]
        lines += [f"  - {v.get('name')} ({v.get('kind')}): {v.get('fit')}" for v in it.get("vendors") or []]
        lines += ["", "The 20% that gives 80%:"] + [f"  - {p}" for p in it.get("pareto") or []]
        lines += ["", f"RFP pack:  ./securax govern rfp {key}"]
        return "\n".join(lines)
    r = next((r for r in cat["roles"] if r["id"] == key), None)
    if r:
        it = rk["roles"].get(key) or {}
        lines = [r["name"], "", it.get("purpose", ""), f"Salary: {it.get('salary', '')}", f"Experience: {it.get('experience', '')}",
                 "", "Must have:"] + [f"  - {m}" for m in it.get("must") or []] + ["", "Interview:"] + [f"  - {q}" for q in it.get("interview") or []]
        return "\n".join(lines)
    ids = [c["id"] for c in cat["capabilities"]] + [r["id"] for r in cat["roles"]]
    close = [i for i in ids if key.lower() in i.lower()]
    raise KeyError(f"no capability or role {key!r}" + (f"; did you mean: {', '.join(close[:6])}" if close else "; see  ./securax govern list"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reckon")
    r.add_argument("id")
    f = sub.add_parser("rfp")
    f.add_argument("id")
    f.add_argument("--out")
    f.add_argument("--org", default="[Organisation]")
    b = sub.add_parser("reckoner")
    b.add_argument("--out")
    sub.add_parser("check")
    a = ap.parse_args(argv)
    rk = load()
    if a.cmd == "reckon":
        try:
            print(card_text(a.id, rk))
        except KeyError as e:
            print(f"✗ {e.args[0]}")
            return 2
        return 0
    if a.cmd == "rfp":
        c = next((c for c in _govern().catalog()["capabilities"] if c["id"] == a.id), None)
        if not c:
            print(f"✗ no capability {a.id!r}; see  ./securax govern list")
            return 2
        p = pathlib.Path(a.out or f"rfp-{a.id}.md")
        p.write_text(rfp_md(c, rk["caps"].get(a.id) or {}, rk["as_of"].get(a.id, ""), a.org), "utf-8")
        print(f"✔ written: {p}  (a draft: review with procurement and legal, and replace each [bracket])")
        return 0
    if a.cmd == "reckoner":
        out = pathlib.Path(a.out) if a.out else OUT
        print(f"✔ {build(out, rk)} pages in {out}")
        return 0
    probs = problems(rk)
    for p in probs:
        print("✗ " + p)
    print("✔ every capability and role has a complete entry" if not probs else f"{len(probs)} gap(s)")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
