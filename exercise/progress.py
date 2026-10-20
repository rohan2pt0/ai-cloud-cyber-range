"""Progress, the way training platforms make it visible: XP and a level per person, badges for real achievements, and how far
the team is along each skill track (doc 81).

XP comes only from work a judge accepted (the points awarded), plus 10 per team-plan item a person closed and 5 per staff
password change they documented. Nothing is earned by clicking. Badges are named for what was done, and each one says why.
"""
from __future__ import annotations

import json
import pathlib

from . import frameworks as fw

TRACKS = pathlib.Path(__file__).resolve().parent / "tracks.json"


def _tracks() -> dict:
    return json.loads(TRACKS.read_text("utf-8"))


def level(xp: float, levels: list | None = None) -> dict:
    levels = levels or _tracks()["levels"]
    cur = [lv for lv in levels if xp >= lv[0]][-1]
    nxt = next((lv for lv in levels if lv[0] > xp), None)
    return {"name": cur[1], "at": cur[0], "next": nxt[1] if nxt else None, "next_at": nxt[0] if nxt else None}


def _who(actor: str, team: int) -> str | None:
    pre = f"blue-{team}:"
    return actor[len(pre):] if actor and actor.startswith(pre) else None


def players(game, team: int) -> list[dict]:
    cat = fw.load()
    names = set(game.players(team))
    stats = {n: {"player": n, "xp": 0.0, "accepted": {"task": 0, "incident": 0, "sitrep": 0}, "detected": set(), "applied": set(), "plan_done": 0, "creds": 0}
             for n in names}
    for s in game.submissions(team):
        n = _who(s["actor"], team)
        if n not in stats or s["status"] != "graded" or s["verdict"] != "accepted":
            continue
        st = stats[n]
        st["xp"] += s["points"] or 0
        st["accepted"][s["kind"]] += 1
        if s["kind"] == "incident":
            st["detected"].update(s["body"].get("techniques", []))
            st["applied"].update(s["body"].get("defences", []))
    for r in game.db.execute("SELECT actor FROM plan WHERE team=? AND status='done'", (team,)):
        n = _who(r["actor"], team)
        if n in stats:
            stats[n]["plan_done"] += 1
            stats[n]["xp"] += 10
    for c in game.creds(team):
        n = _who(c["actor"], team)
        if n in stats:
            stats[n]["creds"] += 1
            stats[n]["xp"] += 5
    out = []
    for st in stats.values():
        tactics = {t for i in st["detected"] if fw.kind_of(i) == "attack" and i in cat["attack"] for t in cat["attack"][i]["tactics"]}
        harden = [i for i in st["applied"] if fw.kind_of(i) == "d3fend" and i in cat["d3fend"] and cat["d3fend"][i]["tactic"] == "Harden"]
        ai = [i for i in st["detected"] | st["applied"] if fw.kind_of(i) == "atlas"]
        badges = []
        if st["accepted"]["incident"]:
            badges.append(("First detection", "an incident report of yours was accepted"))
        techs = [i for i in st["detected"] if fw.kind_of(i) == "attack"]
        if len(techs) >= 3 and len(tactics) >= 3:
            badges.append(("Tactician", f"you detected {len(techs)} ATT&CK techniques across {len(tactics)} tactics"))
        if len(harden) >= 5:
            badges.append(("Hardener", f"you applied {len(harden)} D3FEND hardening techniques"))
        if ai:
            badges.append(("AI defender", "you detected or defended an ATLAS technique"))
        if st["accepted"]["sitrep"] >= 3:
            badges.append(("Reporter", "three of your situation reports were accepted"))
        if st["plan_done"] >= 5:
            badges.append(("Planner", "you closed five team-plan items"))
        out.append({"player": st["player"], "xp": round(st["xp"], 1), "level": level(st["xp"]), "accepted": st["accepted"],
                    "badges": [{"name": b, "why": w} for b, w in badges], "plan_done": st["plan_done"], "creds_documented": st["creds"]})
    return sorted(out, key=lambda x: (-x["xp"], x["player"]))


def tracks(game, team: int) -> list[dict]:
    cov = {r["id"]: r for r in fw.coverage(game, team)["rows"]}
    accepted_reports = sum(1 for s in game.submissions(team) if s["kind"] in ("incident", "sitrep") and s["status"] == "graded" and s["verdict"] == "accepted")
    out = []
    for t in _tracks()["tracks"]:
        items = []
        for i in t["ids"]:
            c = cov.get(i, {})
            items.append({**fw.lookup(i), "met": bool(c.get("met") or c.get("detected")), "detected": bool(c.get("detected")), "applied": bool(c.get("applied"))})
        done = sum(1 for x in items if x["detected"] or x["applied"])
        pct = round(100 * done / len(items)) if items else min(100, accepted_reports * 20)
        out.append({**{k: t[k] for k in ("id", "title", "why", "practise", "certifications")}, "items": items, "progress_pct": pct})
    return out
