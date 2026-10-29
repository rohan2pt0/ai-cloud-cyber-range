#!/usr/bin/env python3
"""`./securax playbook` — run an incident-response playbook as a live, ticked checklist (doc 123).

Mattermost has Playbooks: a template you start as a "run", tick through, and close with a retrospective. This is the
sovereign version for a SOC — the scenarios live in governance/playbooks.json and the steps point at the estate's own
commands (respond, incident, findings, backup/restore), and the run ends by writing a blameless postmortem.

  ./securax playbook list                                  the library (ransomware, data-exfiltration, zero-day, …)
  ./securax playbook start <scenario> "<title>"            begin a run: the ordered checklist, the first move
  ./securax playbook status [<run>]                        progress of a run (latest if none named)
  ./securax playbook step <run> <step-id> [--by WHO]       tick a step done (records who and when)
  ./securax playbook retro <run> [--force]                 close it: write the postmortem (needs the critical steps done)

Runs are stored in vault/playbook-runs/ (private, in your backups, never in git). Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB = ROOT / "governance" / "playbooks.json"
RUNS = ROOT / "vault" / "playbook-runs"
PHASES = ["triage", "contain", "eradicate", "recover", "report", "learn"]


def library() -> dict:
    return json.loads(LIB.read_text("utf-8"))["playbooks"]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "run"


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def run_path(run_id: str) -> pathlib.Path:
    return RUNS / f"{run_id}.json"


def load_run(run_id: str) -> dict:
    return json.loads(run_path(run_id).read_text("utf-8"))


def save_run(run: dict) -> pathlib.Path:
    RUNS.mkdir(parents=True, exist_ok=True)
    p = run_path(run["id"])
    p.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    return p


def latest_run() -> str | None:
    if not RUNS.exists():
        return None
    runs = sorted(RUNS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0].stem if runs else None


def start(scenario: str, title: str) -> dict:
    lib = library()
    if scenario not in lib:
        raise KeyError(f"unknown playbook '{scenario}'. Options: {', '.join(lib)}")
    pb = lib[scenario]
    run = {
        "id": f"{now():%Y%m%d-%H%M}-{scenario}-{slug(title)}",
        "playbook": scenario,
        "name": pb["name"],
        "title": title,
        "opened_at": now().isoformat(timespec="seconds"),
        "closed_at": "",
        "postmortem": "",
        "steps": [{"id": s["id"], "phase": s["phase"], "title": s["title"], "how": s["how"],
                   "critical": bool(s.get("critical")), "done_at": "", "by": ""} for s in pb["steps"]],
    }
    save_run(run)
    return run


def mark(run_id: str, step_id: str, by: str = "") -> dict:
    run = load_run(run_id)
    step = next((s for s in run["steps"] if s["id"] == step_id), None)
    if step is None:
        raise KeyError(f"no step '{step_id}' in run {run_id}. Steps: {', '.join(s['id'] for s in run['steps'])}")
    step["done_at"] = now().isoformat(timespec="seconds")
    step["by"] = by
    save_run(run)
    return run


def progress(run: dict) -> dict:
    done = [s for s in run["steps"] if s["done_at"]]
    crit_open = [s for s in run["steps"] if s["critical"] and not s["done_at"]]
    nxt = next((s for s in run["steps"] if not s["done_at"]), None)
    return {"done": len(done), "total": len(run["steps"]), "critical_open": crit_open, "next": nxt,
            "complete": not crit_open}


def retro(run_id: str, force: bool = False) -> dict:
    run = load_run(run_id)
    pr = progress(run)
    if pr["critical_open"] and not force:
        raise RuntimeError("critical steps are still open: " + ", ".join(s["id"] for s in pr["critical_open"])
                           + " — finish them, or pass --force to close anyway.")
    pm = importlib.util.spec_from_file_location("playbook_postmortem", ROOT / "governance" / "postmortem.py")
    mod = importlib.util.module_from_spec(pm)
    pm.loader.exec_module(mod)
    sev = "sev1" if run["playbook"] in ("ransomware", "data-exfiltration") else "sev2"
    path = mod.new(f"{run['name']}: {run['title']}", sev)
    # seed the postmortem's timeline with the run's ticked steps, so the retro starts from what actually happened
    try:
        text = path.read_text("utf-8")
        timeline = "\n".join(f"- {s['done_at']} — {s['title']}" + (f" (by {s['by']})" if s["by"] else "")
                             for s in run["steps"] if s["done_at"]) or "- (no steps were ticked on the run)"
        if "## Timeline" in text:
            text = text.replace("## Timeline", "## Timeline\n\n_From playbook run " + run["id"] + ":_\n" + timeline, 1)
        else:
            text += "\n## Timeline (from playbook run " + run["id"] + ")\n\n" + timeline + "\n"
        path.write_text(text, encoding="utf-8")
    except Exception:  # noqa: BLE001 - seeding is a convenience; the postmortem is written either way
        pass
    run["closed_at"] = now().isoformat(timespec="seconds")
    run["postmortem"] = str(path.relative_to(ROOT))
    save_run(run)
    return {"run": run, "postmortem": run["postmortem"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax playbook", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    s = sub.add_parser("start"); s.add_argument("scenario"); s.add_argument("title")
    st = sub.add_parser("status"); st.add_argument("run", nargs="?", default="")
    sp = sub.add_parser("step"); sp.add_argument("run"); sp.add_argument("step"); sp.add_argument("--by", default="")
    rt = sub.add_parser("retro"); rt.add_argument("run"); rt.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "list":
        for k, pb in library().items():
            crit = sum(bool(s.get("critical")) for s in pb["steps"])
            print(f"  {k:<18} {pb['name']} — {pb['scenario']}  ({len(pb['steps'])} steps, {crit} critical)")
        print("\nStart one:  ./securax playbook start <scenario> \"what happened\"")
        return 0

    if a.cmd == "start":
        run = start(a.scenario, a.title)
        print(f"▶ playbook run {run['id']}  —  {run['name']}: {run['title']}\n")
        for s in run["steps"]:
            print(f"  [ ] {s['id']:<16} ({s['phase']}{'*' if s['critical'] else ''})  {s['title']}")
            print(f"        → {s['how']}")
        print(f"\nTick a step:  ./securax playbook step {run['id']} <step-id> --by <who>")
        print(f"Close it:     ./securax playbook retro {run['id']}   (* = must be done first)")
        return 0

    run_id = a.run or latest_run() if a.cmd in ("status", "step", "retro") else ""
    if a.cmd in ("status",) and not run_id:
        print("No playbook runs yet. Start one:  ./securax playbook start <scenario> \"what happened\"")
        return 0
    if not run_id:
        ap.error("name a run")

    if a.cmd == "step":
        run = mark(run_id, a.step, a.by)
        pr = progress(run)
        print(f"✔ {a.step} done ({pr['done']}/{pr['total']}).")
        if pr["next"]:
            print(f"Next: [{pr['next']['id']}] {pr['next']['title']}\n  → {pr['next']['how']}")
        elif pr["complete"]:
            print(f"All steps done. Close it:  ./securax playbook retro {run_id}")
        return 0

    if a.cmd == "retro":
        try:
            out = retro(run_id, a.force)
        except RuntimeError as e:
            print(f"✗ {e}")
            return 1
        print(f"✔ run {run_id} closed. Postmortem written: {out['postmortem']}")
        print("  Fill it in while it is fresh; its actions are tracked by  ./securax postmortem actions")
        print("  Then keep the root cause closed for good:  ./securax adversary")
        return 0

    # status
    run = load_run(run_id)
    pr = progress(run)
    opened = run["opened_at"]
    print(f"Playbook run {run_id}  —  {run['name']}: {run['title']}")
    print(f"opened {opened}" + (f" · closed {run['closed_at']}" if run["closed_at"] else "") + f" · {pr['done']}/{pr['total']} steps done")
    for s in run["steps"]:
        box = "x" if s["done_at"] else " "
        when = f"  ({s['done_at']}" + (f", {s['by']}" if s["by"] else "") + ")" if s["done_at"] else ""
        print(f"  [{box}] {s['id']:<16} ({s['phase']}{'*' if s['critical'] else ''})  {s['title']}{when}")
    if pr["critical_open"]:
        print("\nStill to do (critical): " + ", ".join(s["id"] for s in pr["critical_open"]))
    elif not run["closed_at"]:
        print(f"\nAll critical steps done — close it:  ./securax playbook retro {run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
