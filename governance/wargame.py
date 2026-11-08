#!/usr/bin/env python3
"""`./securax wargame` — rehearse the coordination of a cyber crisis as a timed tabletop, and score it (doc 126).

The hard part of a real crisis is not the attack: it is the coordination — the right action reaching the right team
in time while deadlines collide, a key person is on leave, and a second hit lands mid-response. You cannot practise
that from a document. This runs a scenario as a timeline of injects (a thing that happens, owned by a team, with an
expected action and an SLA), you respond to each in free text, and the estate scores whether the right action reached
the right owner in time — then writes an after-action report with the coordination gaps and the improvement actions.

  ./securax wargame list                                   the scenario library (what each one rehearses, and its worst-cases)
  ./securax wargame start <scenario> [--title "<t>"]       begin a run; the clock starts at t=0 and the first inject fires
  ./securax wargame now [<id>]                             what is happening right now — every live inject you have not answered
  ./securax wargame respond <id> <inject> --action "<what you did>" [--minutes N]   record and score your response
  ./securax wargame advance [<id>] [--to <min>|--by <min>] move the clock to the next inject (or a given minute) and fire what is due
  ./securax wargame status [<id>] [--json]                 the timeline: fired / live / answered, the score so far, the clock
  ./securax wargame aar [<id>] [--save] [--lessons]        the after-action report: per-inject scores, coordination gaps, improvement actions

Scoring is deterministic (a keyword rubric against each inject's expected action, plus timeliness against its SLA), so
it runs the same offline and in a test. When a gateway is configured it ALSO asks a model to grade the free text and to
play the inject's sender under pressure — inheriting the gateway's rails and audit trail — but the deterministic score
is always the score of record. Runs are stored in vault/wargame-runs/ (private, never in git). The scenarios are DATA
(governance/wargames.json) — add your own. Pairs with ./securax crisis (the real coordination) and ./securax continuity
(the technical tabletop). Standard library only. A rehearsal, not a substitute for a real exercise programme.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
LIB = HERE / "wargames.json"
UTC = dt.timezone.utc

_STOP = {
    "the", "and", "for", "with", "your", "you", "are", "all", "who", "not", "let", "who", "its", "it", "a", "an",
    "to", "do", "of", "in", "on", "or", "is", "be", "no", "as", "at", "by", "if", "so", "up", "out", "get", "has",
    "one", "two", "that", "this", "them", "they", "then", "than", "from", "into", "each", "more", "most", "will",
    "can", "any", "per", "via", "etc", "name", "keep", "make", "take", "give", "show", "does",
}


def lib() -> dict:
    return json.loads(LIB.read_text("utf-8"))


def runs_dir() -> pathlib.Path:
    base = pathlib.Path(os.environ.get("SECURAX_WARGAME_DIR") or (ROOT / "vault" / "wargame-runs"))
    base.mkdir(parents=True, exist_ok=True)
    return base


def tz() -> dt.tzinfo:
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(os.environ.get("SECURAX_TZ", "Asia/Kolkata"))
    except Exception:  # noqa: BLE001
        return dt.timezone(dt.timedelta(hours=5, minutes=30))


def iso(t: dt.datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(s: str) -> str:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(tz()).strftime("%d %b %Y %H:%M %Z")


def run_path(rid: str) -> pathlib.Path:
    return runs_dir() / f"{rid}.json"


def load_run(rid: str) -> dict:
    p = run_path(rid)
    if not p.exists():
        raise SystemExit(f"no such wargame run {rid} (see: ./securax wargame status)")
    return json.loads(p.read_text("utf-8"))


def save_run(run: dict) -> None:
    p = run_path(run["id"])
    p.write_text(json.dumps(run, indent=1) + "\n", "utf-8")
    os.chmod(p, 0o600)


def runs() -> list[dict]:
    return sorted((json.loads(p.read_text("utf-8")) for p in runs_dir().glob("WARGAME-*.json")), key=lambda r: r["id"])


def _keywords(text: str) -> list[str]:
    """Content words from an expected-action string, for the rubric. Deliberately simple and deterministic."""
    words = re.findall(r"[a-z0-9][a-z0-9/\-]+", text.lower())
    seen, out = set(), []
    for w in words:
        w = w.strip("/-")
        if len(w) >= 3 and w not in _STOP and w not in seen:
            seen.add(w)
            out.append(w)
    return out


def _stem(w: str) -> str:
    for suf in ("ing", "ers", "er", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def score_response(inject: dict, action: str, acted_min: int) -> dict:
    """Deterministic rubric: correctness = keyword overlap vs the expected action; timeliness vs the SLA."""
    keys = _keywords(inject["expect"])
    atoks = {_stem(w) for w in re.findall(r"[a-z0-9][a-z0-9/\-]+", action.lower())}
    matched = [k for k in keys if _stem(k) in atoks or k in action.lower()]
    missed = [k for k in keys if k not in matched]
    correctness = round(len(matched) / len(keys), 3) if keys else 0.0
    elapsed = max(0, acted_min - int(inject.get("at_min", 0)))
    sla = int(inject.get("sla_min", 60)) or 60
    if elapsed <= sla:
        timeliness = 1.0
    else:
        timeliness = round(max(0.0, 1 - (elapsed - sla) / (2 * sla)), 3)
    score = round(0.6 * correctness + 0.4 * timeliness, 3)
    return {"score": score, "correctness": correctness, "timeliness": timeliness,
            "matched": matched, "missed": missed, "elapsed_min": elapsed, "sla_min": sla, "on_time": elapsed <= sla}


def _ai_grade(inject: dict, action: str) -> dict | None:
    """Optional: ask the configured gateway to grade the free text and to reply AS the sender under pressure.
    Offline-safe — returns None with no GATEWAY_URL or on any error; the deterministic rubric is the score of record."""
    if not os.getenv("GATEWAY_URL"):
        return None
    try:
        spec = importlib.util.spec_from_file_location("wargame_personas", ROOT / "agents" / "personas.py")
        personas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(personas)
        q = (
            "You are grading one response in a cyber-crisis coordination tabletop, then role-playing the sender.\n"
            f"The inject (from {inject['from']}, owner team: {inject['owner']}): {inject['text']}\n"
            f"The expected action was: {inject['expect']}\n"
            f"The responder wrote: {action}\n\n"
            "Reply in two short lines, nothing else:\n"
            "GRADE: <0-100> — <one sentence: what was right, what was missing>\n"
            "SENDER: <one sentence, in character as the sender above, pressing for what is still owed>"
        )
        res = personas.ask_agent("negotiation", q, careful=False)
        ans = res.get("answer")
        if not ans:
            return None
        grade, sender = None, None
        for ln in ans.splitlines():
            m = re.match(r"\s*GRADE:\s*(\d{1,3})", ln, re.I)
            if m:
                grade = max(0, min(100, int(m.group(1))))
            if ln.strip().upper().startswith("SENDER:"):
                sender = ln.split(":", 1)[1].strip()
        return {"grade": grade, "sender": sender, "raw": ans.strip()[:600]}
    except Exception:  # noqa: BLE001
        return None


def _live(run: dict) -> list[dict]:
    """Injects that have fired (at_min <= now_min) and are not yet answered."""
    return [i for i in run["injects"]
            if int(i["at_min"]) <= run["now_min"] and i["id"] not in run["responses"]]


def _fired(run: dict) -> list[dict]:
    return [i for i in run["injects"] if int(i["at_min"]) <= run["now_min"]]


def cmd_list(a, now: dt.datetime) -> int:
    data = lib()
    print(data["about"])
    print("\nScenarios (./securax wargame start <id>):\n")
    for sid, sc in data["scenarios"].items():
        print(f"  {sid:<16} {sc['name']}  ({len(sc['injects'])} injects)")
        print(f"       {sc['about']}")
        for w in sc.get("worst_case", []):
            print(f"       worst-case: {w}")
        print()
    return 0


def _new_id(now: dt.datetime) -> str:
    n = 1 + sum(1 for r in runs() if r["id"].startswith(f"WARGAME-{now:%Y%m%d}"))
    return f"WARGAME-{now:%Y%m%d}-{n:03d}"


def cmd_start(a, now: dt.datetime) -> int:
    data = lib()
    if a.scenario not in data["scenarios"]:
        print(f"unknown scenario {a.scenario!r}; known: {', '.join(data['scenarios'])}")
        return 2
    sc = data["scenarios"][a.scenario]
    injects = sorted(sc["injects"], key=lambda i: int(i["at_min"]))
    run = {"id": _new_id(now), "scenario": a.scenario, "name": sc["name"], "title": a.title or sc["name"],
           "owners": data["owners"], "worst_case": sc.get("worst_case", []),
           "started_at": iso(now), "now_min": 0, "responses": {}, "injects": injects}
    save_run(run)
    print(f"▶ Wargame {run['id']} — {run['name']}")
    print(f"  {sc['about']}")
    print(f"  {len(injects)} injects over {injects[-1]['at_min']} minutes. The clock is at t=0.\n")
    _print_live(run)
    print("\n  Respond to each:  ./securax wargame respond " + run["id"] + " <inject> --action \"<what you did>\"")
    print("  Move the clock:   ./securax wargame advance " + run["id"] + "    (fires the next inject)")
    return 0


def _print_live(run: dict) -> None:
    owners = run["owners"]
    live = _live(run)
    if not live:
        nxt = next((i for i in run["injects"] if int(i["at_min"]) > run["now_min"]), None)
        if nxt:
            print(f"  Nothing live at t={run['now_min']}m. Next inject {nxt['id']} fires at t={nxt['at_min']}m "
                  f"→ advance:  ./securax wargame advance {run['id']}")
        else:
            print(f"  All {len(run['injects'])} injects fired and answered. Write the report:  ./securax wargame aar {run['id']}")
        return
    print(f"  ⏱  t={run['now_min']}m — {len(live)} inject(s) live and unanswered:")
    for i in live:
        wc = "  ⚠ WORST CASE" if "WORST CASE" in i["text"] else ""
        who = owners.get(i["owner"], i["owner"])
        print(f"\n    ── {i['id']}  [{i['severity']}]  from {i['from']}  ·  owner: {who}  ·  SLA {i['sla_min']}m{wc}")
        print(f"       {i['text']}")
        if i.get("hint"):
            print(f"       hint: {i['hint']}")


def cmd_now(a, now: dt.datetime) -> int:
    run = _pick(a)
    if run is None:
        return 2
    print(f"▶ {run['id']}  {run['name']}  (clock at t={run['now_min']}m)")
    _print_live(run)
    return 0


def cmd_advance(a, now: dt.datetime) -> int:
    run = _pick(a)
    if run is None:
        return 2
    before = run["now_min"]
    if a.to is not None:
        target = int(a.to)
    elif a.by is not None:
        target = run["now_min"] + int(a.by)
    else:
        future = [int(i["at_min"]) for i in run["injects"] if int(i["at_min"]) > run["now_min"]]
        if not future:
            print(f"  The clock is at t={run['now_min']}m and no inject fires later. "
                  f"Answer what is live, then:  ./securax wargame aar {run['id']}")
            _print_live(run)
            return 0
        target = min(future)
    run["now_min"] = max(run["now_min"], target)
    save_run(run)
    print(f"▶ {run['id']} — clock {before}m → {run['now_min']}m")
    _print_live(run)
    return 0


def cmd_respond(a, now: dt.datetime) -> int:
    run = load_run(a.id)
    inj = next((i for i in run["injects"] if i["id"] == a.inject), None)
    if inj is None:
        print(f"no inject {a.inject!r} in {run['id']}; injects: {', '.join(i['id'] for i in run['injects'])}")
        return 2
    acted = a.minutes if a.minutes is not None else run["now_min"]
    if int(inj["at_min"]) > acted:
        print(f"  inject {inj['id']} fires at t={inj['at_min']}m; you cannot answer it at t={acted}m.")
        return 2
    run["now_min"] = max(run["now_min"], acted)
    sc = score_response(inj, a.action, acted)
    rec = {"action": a.action, "at_min": acted, **sc, "recorded_at": iso(now)}
    ai = _ai_grade(inj, a.action)
    if ai:
        rec["ai"] = ai
    run["responses"][inj["id"]] = rec
    save_run(run)
    bar = "✅" if sc["score"] >= 0.75 else ("🟡" if sc["score"] >= 0.5 else "🔴")
    ontime = "on time" if sc["on_time"] else f"LATE (SLA {sc['sla_min']}m, took {sc['elapsed_min']}m)"
    print(f"{bar} {inj['id']} scored {int(sc['score'] * 100)}/100  —  correctness {int(sc['correctness'] * 100)}%, {ontime}")
    if sc["missed"]:
        print(f"   you did not cover: {', '.join(sc['missed'])}")
        print(f"   expected: {inj['expect']}")
    if ai and ai.get("sender"):
        print(f"   ⤷ {inj['from']} presses: {ai['sender']}")
    live = _live(run)
    if live:
        print(f"\n   {len(live)} still live → ./securax wargame now {run['id']}")
    else:
        nxt = next((i for i in run["injects"] if int(i["at_min"]) > run["now_min"]), None)
        print(f"\n   next inject at t={nxt['at_min']}m → ./securax wargame advance {run['id']}" if nxt
              else f"\n   all injects answered → ./securax wargame aar {run['id']}")
    return 0


def cmd_status(a, now: dt.datetime) -> int:
    run = _pick(a, allow_none=True)
    if run is None:
        rs = runs()
        if not rs:
            print("No wargame runs yet. Begin one:  ./securax wargame start <scenario>   "
                  "(scenarios: " + ", ".join(lib()["scenarios"]) + ")")
            return 0
        for r in rs:
            ans = len(r["responses"])
            tot = len(r["injects"])
            sc = _overall(r)
            print(f"  {r['id']}  {r['name']:<34} t={r['now_min']}m  {ans}/{tot} answered  score {int(sc * 100)}")
        return 0
    if a.json:
        print(json.dumps(run, indent=2))
        return 0
    owners = run["owners"]
    print(f"▶ {run['id']}  {run['name']}  —  started {local(run['started_at'])}")
    print(f"  clock at t={run['now_min']}m   ·   score so far {int(_overall(run) * 100)}/100")
    for i in run["injects"]:
        who = owners.get(i["owner"], i["owner"])
        if i["id"] in run["responses"]:
            r = run["responses"][i["id"]]
            bar = "✅" if r["score"] >= 0.75 else ("🟡" if r["score"] >= 0.5 else "🔴")
            tag = f"{int(r['score'] * 100):>3}/100 {'on-time' if r['on_time'] else 'LATE'}"
        elif int(i["at_min"]) <= run["now_min"]:
            bar, tag = "⏱", "LIVE — unanswered"
        else:
            bar, tag = "⬜", f"fires t={i['at_min']}m"
        print(f"  {bar} t={int(i['at_min']):>3}m  {i['id']:<4} [{i['severity']:<8}] {who:<28} {tag}")
    live = _live(run)
    if live:
        print(f"\n  ▶ {len(live)} live now → ./securax wargame now {run['id']}")
    return 0


def _overall(run: dict) -> float:
    """Mean inject score; an unanswered inject that has already fired counts as 0 (a missed coordination)."""
    scores = []
    for i in run["injects"]:
        if i["id"] in run["responses"]:
            scores.append(run["responses"][i["id"]]["score"])
        elif int(i["at_min"]) <= run["now_min"]:
            scores.append(0.0)
    return round(sum(scores) / len(scores), 3) if scores else 0.0


def _aar(run: dict, now: dt.datetime) -> str:
    owners = run["owners"]
    overall = _overall(run)
    answered = [i for i in run["injects"] if i["id"] in run["responses"]]
    fired = _fired(run)
    missed = [i for i in fired if i["id"] not in run["responses"]]
    on_time = sum(1 for i in answered if run["responses"][i["id"]]["on_time"])
    out = [f"# After-action report — {run['id']}", "",
           f"**Scenario:** {run['name']}  ·  **Title:** {run['title']}",
           f"**Run:** started {local(run['started_at'])}, clock reached t={run['now_min']}m",
           f"**Overall coordination score:** {int(overall * 100)}/100",
           f"**Injects:** {len(answered)}/{len(fired)} fired injects answered; {on_time}/{len(answered)} on time; "
           f"{len(missed)} missed.", "",
           "## Timeline and scores", "",
           "| t | Inject | From | Owner | Score | On time | Expected action |",
           "|---|---|---|---|---|---|---|"]
    for i in run["injects"]:
        if int(i["at_min"]) > run["now_min"]:
            continue
        who = owners.get(i["owner"], i["owner"])
        if i["id"] in run["responses"]:
            r = run["responses"][i["id"]]
            out.append(f"| {i['at_min']}m | {i['id']} | {i['from']} | {who} | {int(r['score'] * 100)} | "
                       f"{'yes' if r['on_time'] else 'LATE'} | {i['expect']} |")
        else:
            out.append(f"| {i['at_min']}m | {i['id']} | {i['from']} | {who} | 0 (missed) | — | {i['expect']} |")

    gaps = []
    for i in fired:
        if i["id"] not in run["responses"]:
            gaps.append((i, "no response — the inject went unanswered"))
        else:
            r = run["responses"][i["id"]]
            if not r["on_time"]:
                gaps.append((i, f"answered LATE — SLA {r['sla_min']}m, took {r['elapsed_min']}m"))
            elif r["correctness"] < 0.6:
                gaps.append((i, f"incomplete — missed: {', '.join(r['missed']) or '(low keyword match)'}"))
    out += ["", "## Coordination gaps", ""]
    if gaps:
        for i, why in gaps:
            who = owners.get(i["owner"], i["owner"])
            out.append(f"- **{i['id']} ({who})** — {why}")
            wc = "WORST CASE: " in i["text"] or "WORST CASE" in i["text"]
            if wc:
                out.append("  - this was a designed worst-case; it is exactly the moment a real crisis fails.")
    else:
        out.append("- None. Every fired inject was answered on time and on point. Raise the difficulty: a tighter clock, fewer people.")

    out += ["", "## Improvement actions (owned, specific)", ""]
    if gaps:
        for n, (i, _why) in enumerate(gaps, 1):
            who = owners.get(i["owner"], i["owner"])
            out.append(f"{n}. **{who}** — rehearse until this is reflex: {i['expect']}"
                       + (f"  (do it with: {i['hint']})" if i.get("hint") else ""))
    else:
        out.append("1. Keep the drill in the weekly rhythm; rotate who runs it so no single coordinator is the dependency.")
    out += ["", "## Worst-cases this scenario builds in", ""]
    for w in run.get("worst_case", []):
        out.append(f"- {w}")
    out += ["", "_A rehearsal, not a real exercise. Carry the improvement actions into ./securax crisis and the next drill._"]
    return "\n".join(out) + "\n"


def cmd_aar(a, now: dt.datetime) -> int:
    run = _pick(a)
    if run is None:
        return 2
    report = _aar(run, now)
    print(report)
    if a.save:
        out = runs_dir() / run["id"] / "after-action-report.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, "utf-8")
        os.chmod(out, 0o600)
        print(f"\n[saved] {out}")
    if a.lessons:
        gaps = [i for i in _fired(run)
                if i["id"] not in run["responses"] or not run["responses"][i["id"]]["on_time"]
                or run["responses"][i["id"]]["correctness"] < 0.6]
        if gaps:
            print("\nTurn each gap into a standing lesson (review, then run):")
            for i in gaps:
                owner = run["owners"].get(i["owner"], i["owner"])
                print(f"  ./securax lessons add \"wargame {run['scenario']}/{i['id']}: {owner} must — {i['expect']}\"")
        else:
            print("\nNo gaps to turn into lessons — clean run.")
    return 0


def _pick(a, allow_none: bool = False) -> dict | None:
    rid = getattr(a, "id", None)
    if rid:
        return load_run(rid)
    rs = runs()
    if not rs:
        if allow_none:
            return None
        print("No wargame runs yet. Begin one:  ./securax wargame start <scenario>")
        return None
    if allow_none and len(rs) > 1:
        return None
    return rs[-1]        # the most recent run, when no id is given


def main(argv: list[str] | None = None, now: dt.datetime | None = None) -> int:
    now = now or dt.datetime.now(UTC)
    ap = argparse.ArgumentParser(prog="wargame", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sr = sub.add_parser("start")
    sr.add_argument("scenario")
    sr.add_argument("--title", default="")
    nw = sub.add_parser("now")
    nw.add_argument("id", nargs="?")
    av = sub.add_parser("advance")
    av.add_argument("id", nargs="?")
    av.add_argument("--to", type=int, default=None)
    av.add_argument("--by", type=int, default=None)
    rs = sub.add_parser("respond")
    rs.add_argument("id")
    rs.add_argument("inject")
    rs.add_argument("--action", required=True)
    rs.add_argument("--minutes", type=int, default=None)
    st = sub.add_parser("status")
    st.add_argument("id", nargs="?")
    st.add_argument("--json", action="store_true")
    ar = sub.add_parser("aar")
    ar.add_argument("id", nargs="?")
    ar.add_argument("--save", action="store_true")
    ar.add_argument("--lessons", action="store_true")
    a = ap.parse_args(argv)
    fn = {"list": cmd_list, "start": cmd_start, "now": cmd_now, "advance": cmd_advance,
          "respond": cmd_respond, "status": cmd_status, "aar": cmd_aar}[a.cmd]
    return fn(a, now)


if __name__ == "__main__":
    sys.exit(main())
