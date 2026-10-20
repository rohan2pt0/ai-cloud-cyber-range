"""MITRE ATT&CK, D3FEND and ATLAS in the exercise range: one vocabulary for what happened, what defended, and what to study.

Every task, attack report and incident report can name the adversary behaviour (ATT&CK technique, or ATLAS for attacks on
AI systems) and the defence used (D3FEND technique, or an ATLAS mitigation). The portal then shows a learner, per tactic:
what the exercise threw at them, what they detected, and which defences they applied, each linked to MITRE's own page.

frameworks.json holds only the identifiers the range uses, with their official names, taken from MITRE's data:
    ATT&CK Enterprise  github.com/mitre-attack/attack-stix-data  (© MITRE, ATT&CK Terms of Use)
    D3FEND             d3fend.mitre.org/ontologies/d3fend.csv     (© MITRE, MIT licence)
    ATLAS              github.com/mitre-atlas/atlas-data          (© MITRE, Apache 2.0)
`build()` regenerates it from freshly downloaded files, so names follow MITRE when MITRE renames a technique.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
CATALOGUE = HERE / "frameworks.json"
KINDS = ("attack", "d3fend", "atlas")
ATTACK_TACTICS = ["reconnaissance", "resource-development", "initial-access", "execution", "persistence", "privilege-escalation", "stealth",
                  "defense-impairment", "credential-access", "discovery", "lateral-movement", "collection", "command-and-control", "exfiltration", "impact"]
D3FEND_TACTICS = ["Model", "Harden", "Detect", "Isolate", "Deceive", "Evict", "Restore"]


def load() -> dict:
    return json.loads(CATALOGUE.read_text("utf-8"))


def kind_of(ident: str) -> str | None:
    if re.fullmatch(r"T\d{4}(\.\d{3})?", ident):
        return "attack"
    if re.fullmatch(r"D3-[A-Z0-9]+", ident):
        return "d3fend"
    if re.fullmatch(r"AML\.[TM]\d{4}(\.\d{3})?", ident):
        return "atlas"
    return None


def url(ident: str, cat: dict | None = None) -> str:
    k = kind_of(ident)
    if k == "attack":
        return "https://attack.mitre.org/techniques/" + ident.replace(".", "/") + "/"
    if k == "atlas":
        return f"https://atlas.mitre.org/{'mitigations' if ident.startswith('AML.M') else 'techniques'}/{ident}"
    if k == "d3fend":
        return (cat or load())["d3fend"][ident]["url"]
    raise ValueError(f"not a framework identifier: {ident}")


def lookup(ident: str, cat: dict | None = None) -> dict:
    cat = cat or load()
    k = kind_of(ident)
    if not k or ident not in cat[k]:
        raise KeyError(f"{ident} is not in the range's framework catalogue (exercise/frameworks.json)")
    return {"id": ident, "kind": k, **cat[k][ident], "url": url(ident, cat)}


def unknown(idents, cat: dict | None = None) -> list[str]:
    cat = cat or load()
    return [i for i in idents if not kind_of(i) or i not in cat[kind_of(i)]]


def tags(item: dict) -> list[str]:
    return [*item.get("attack", []), *item.get("d3fend", []), *item.get("atlas", [])]


def build(attack_slim: pathlib.Path, d3fend_csv: pathlib.Path, atlas_yaml: pathlib.Path, wanted: list[str]) -> dict:
    """Rebuild the catalogue for `wanted` identifiers from MITRE's files (the ATT&CK one as lifecycle/offline.py slims it)."""
    import yaml  # only for a rebuild; the range itself never needs it
    a = json.loads(attack_slim.read_text("utf-8"))
    rows = list(csv.DictReader(d3fend_csv.open(encoding="utf-8")))
    d3 = {}
    for r in rows:
        name = r["D3FEND Technique"] or r["D3FEND Technique Level 0"] or r["D3FEND Technique Level 1"]
        d3[r["ID"]] = {"name": name, "tactic": r["D3FEND Tactic"], "url": "https://d3fend.mitre.org/technique/d3f:" + name.replace(" ", "") + "/"}
    at = yaml.safe_load(atlas_yaml.read_text("utf-8"))
    m = at["matrices"][0]
    tac = {t["id"]: t["name"] for t in m["tactics"]}
    atl = {t["id"]: {"name": t["name"], "tactics": [tac.get(x, x) for x in t.get("tactics", [])]} for t in m["techniques"]}
    atl.update({x["id"]: {"name": x["name"], "tactics": ["Mitigation"]} for x in (m.get("mitigations") or at.get("mitigations") or [])})
    out = {"about": "Only the identifiers the exercise range uses, with MITRE's official names. Rebuild with exercise.frameworks.build().",
           "versions": {"attack": a.get("attack_version"), "atlas": at.get("version"), "d3fend": "csv export"},
           "licences": {"attack": "© The MITRE Corporation. ATT&CK Terms of Use: https://attack.mitre.org/resources/terms-of-use/",
                        "d3fend": "© The MITRE Corporation, MIT licence", "atlas": "© The MITRE Corporation, Apache 2.0"},
           "attack": {}, "d3fend": {}, "atlas": {}}
    missing = []
    for i in sorted(set(wanted)):
        k = kind_of(i)
        src = {"attack": a["techniques"], "d3fend": d3, "atlas": atl}.get(k or "", {})
        if i not in src:
            missing.append(i)
            continue
        e = src[i]
        out[k][i] = {"name": e["name"], **({"tactics": e["tactics"]} if "tactics" in e else {}), **({"tactic": e["tactic"], "url": e["url"]} if k == "d3fend" else {})}
    if missing:
        raise ValueError("not found in MITRE's data: " + ", ".join(missing))
    return out


def coverage(game, team: int) -> dict:
    """What this team met (tasks, attack reports), detected (accepted incident reports) and applied (defences it named)."""
    cat = load()
    sc = game.scenario(team)
    met, detected, applied = {}, {}, {}
    for t in sc["tasks"]:
        for i in t.get("attack", []) + t.get("atlas", []):
            met.setdefault(i, set()).add(f"task: {t['title']}")
        for i in t.get("d3fend", []):
            met.setdefault(i, set()).add(f"task: {t['title']}")
    for a in game.attacks(team):
        for i in json.loads(a.get("techniques") or "[]"):
            met.setdefault(i, set()).add(f"attack on {a['target']}")
    for s in game.submissions(team, "incident"):
        b = s["body"]
        accepted = s["status"] == "graded" and s["verdict"] == "accepted"
        for i in b.get("techniques", []):
            (detected if accepted else met).setdefault(i, set()).add(f"incident report on {s['ref']}" + ("" if accepted else " (not accepted yet)"))
        for i in b.get("defences", []):
            if accepted:
                applied.setdefault(i, set()).add(f"incident report on {s['ref']}")
    for s in game.submissions(team, "task"):
        if s["status"] == "graded" and s["verdict"] == "accepted":
            t = next((x for x in sc["tasks"] if x["id"] == s["ref"]), {})
            for i in t.get("d3fend", []) + [x for x in t.get("atlas", []) if x.startswith("AML.M")]:
                applied.setdefault(i, set()).add(f"task solved: {t.get('title', s['ref'])}")
    rows = []
    for i in sorted(set(met) | set(detected) | set(applied)):
        try:
            e = lookup(i, cat)
        except KeyError:
            continue
        rows.append({**e, "met": sorted(met.get(i, ())), "detected": sorted(detected.get(i, ())), "applied": sorted(applied.get(i, ()))})
    by = {"attack": {}, "d3fend": {}, "atlas": {}}
    for r in rows:
        groups = r.get("tactics") or [r.get("tactic", "")]
        for g in groups:
            by[r["kind"]].setdefault(g, []).append(r)
    order = {"attack": ATTACK_TACTICS, "d3fend": D3FEND_TACTICS, "atlas": []}
    return {"versions": cat["versions"], "rows": rows,
            "groups": {k: [{"group": g, "items": v} for g, v in sorted(by[k].items(), key=lambda x: (order[k].index(x[0]) if x[0] in order[k] else 99, x[0]))]
                       for k in KINDS},
            "counts": {"met": len([r for r in rows if r["met"] or r["detected"]]), "detected": len([r for r in rows if r["detected"]]),
                       "applied": len([r for r in rows if r["applied"]])}}
