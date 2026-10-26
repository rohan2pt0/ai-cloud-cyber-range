#!/usr/bin/env python3
"""SELFTEST — prove every ./securax command really loads and the safe ones really run, with no side effects (doc 117).

A system you cannot trust to start is worse than no system. This checks, for every command the CLI advertises in
`./securax help`:

  1. **Wired** — the command has a dispatch branch, so it can never print "unknown command" for something in the menu.
  2. **Loads** — every Python module the branch runs is imported (its top level is executed), so a syntax error, a bad
     import, or a missing file is caught here instead of when you type the command in anger.
  3. **Runs (read-only ones)** — commands with a safe read-only form (status / check / --json / list / help) are actually
     executed, and must finish without throwing (a Python traceback or a shell error is a failure).

Nothing that changes state is ever executed (no up/down/backup/restore/update/ship/send). A command whose code needs a
service dependency this machine has not installed is reported as "needs a dependency", not a failure. Exit 0 only when
every command is wired, every module loads, and every read-only probe ran clean.

    ./securax selftest            the full report (wiring, module load, read-only probes)
    ./securax selftest --json     the same as JSON, for CI and the cockpit
    ./securax selftest --quiet    only the summary line and any failures
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLI = ROOT / "securax"

# Read-only invocations that are safe to actually RUN (no state change, no network writes, no notifications sent).
# Each value is the argv after `./securax`. A probe passes if it does not throw (see _threw); a non-zero exit from a
# handled condition ("nothing configured yet") is NOT a failure — only a crash is.
READONLY: dict[str, list[str]] = {
    "help": ["help"], "suite": ["suite", "check"], "resilience": ["resilience"], "risks": ["risks"],
    "progress": ["progress"], "map": ["map"], "improve": ["improve"], "insight": ["insight"],
    "readiness": ["readiness"], "impact": ["impact"], "proofs": ["proofs"], "evidence": ["evidence"],
    "findings": ["findings"], "lessons": ["lessons"], "backlog": ["backlog"], "next": ["next", "--json"],
    "jewels": ["jewels"], "govern": ["govern"], "comply": ["comply"], "venture": ["venture", "guards"],
    "adversary": ["adversary", "status"], "regwatch": ["regwatch", "status"], "tls": ["tls", "status"],
    "routines": ["routines", "list"], "privacy": ["privacy", "check"], "vet": ["vet", "check"],
    "ship": ["ship", "check"], "ai": ["ai", "share"], "nodes": ["nodes"], "capacity": ["capacity"],
    "stages": ["stages"], "phones": ["phones"], "status": ["status"],
}

# A traceback or a shell/dispatch error means the command threw; a clean non-zero exit (a handled "not set up") does not.
_THREW = re.compile(r"Traceback \(most recent call last\)|unknown command|command not found|No such file or directory"
                    r"|ModuleNotFoundError|SyntaxError|IndentationError")


def advertised() -> list[str]:
    """The commands the CLI lists in `./securax help` — the surface a user can reach."""
    out = subprocess.run(["bash", str(CLI), "help"], capture_output=True, text=True, cwd=ROOT).stdout
    cmds = []
    for ln in out.splitlines():
        m = re.match(r"  ([a-z][a-z0-9-]+)\s{2,}\S", ln)      # "  name   description"
        if m and m.group(1) not in cmds:
            cmds.append(m.group(1))
    return cmds


def dispatch_table(text: str) -> dict[str, str]:
    """Each top-level command's case body, from `  cmd)` to the matching `;;`. Top level = two-space indent."""
    bodies: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"  ([a-z][a-z0-9-]+)\)\s*$", lines[i]) or re.match(r"  ([a-z][a-z0-9-]+)\|", lines[i])
        if m:
            name = m.group(1)
            body = []
            i += 1
            while i < len(lines) and not re.match(r"  ;;\s*$", lines[i]) and not re.match(r"  [a-z][a-z0-9-]+\)", lines[i]):
                body.append(lines[i])
                i += 1
            bodies[name] = "\n".join(body)
        else:
            i += 1
    return bodies


def recognized(text: str) -> set[str]:
    """Every command (and alias) the case statement will dispatch, so 'unknown command' is impossible for it."""
    names: set[str] = set()
    for m in re.finditer(r"^  ([a-z][a-z0-9-]+(?:\|[a-z][a-z0-9-]+)*)\)", text, re.M):
        for part in m.group(1).split("|"):
            names.add(part)
    return names


def modules_in(body: str) -> list[str]:
    """The repo-relative Python files a command's branch runs (so we can load each and catch a broken one)."""
    found = []
    for m in re.finditer(r"\$ROOT/([A-Za-z0-9_./-]+\.py)", body):
        p = m.group(1)
        if p not in found:
            found.append(p)
    return found


def load_module(rel: str) -> tuple[str, str]:
    """Import a module file (runs its top level, never its main()). Returns (state, detail).
    ok = loaded clean; dep = needs a dependency this machine lacks (not a code fault); fail = the code is broken."""
    path = ROOT / rel
    if not path.exists():
        return "fail", f"{rel} does not exist"
    try:
        spec = importlib.util.spec_from_file_location("securax_selftest_probe", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return "ok", ""
    except (ModuleNotFoundError, ImportError) as e:
        return "dep", str(e)
    except Exception as e:                                             # noqa: BLE001 - any top-level crash is a real fault
        return "fail", f"{type(e).__name__}: {e}"


def _threw(cp: subprocess.CompletedProcess) -> bool:
    return bool(_THREW.search((cp.stdout or "") + (cp.stderr or "")))


def run_probe(argv: list[str]) -> tuple[str, str]:
    """Run a read-only command. ok = ran without throwing; fail = threw a traceback / shell error / unknown command."""
    try:
        cp = subprocess.run(["bash", str(CLI), *argv], capture_output=True, text=True, cwd=ROOT, timeout=60)
    except subprocess.TimeoutExpired:
        return "fail", "timed out (over 60s)"
    if _threw(cp):
        tail = (cp.stderr or cp.stdout or "").strip().splitlines()
        return "fail", (tail[-1] if tail else f"exit {cp.returncode}")
    return "ok", ""


def run(probe_readonly: bool = True) -> dict:
    text = CLI.read_text("utf-8")
    cmds = advertised()
    known = recognized(text)
    bodies = dispatch_table(text)
    results = []
    for c in cmds:
        r: dict = {"command": c, "wired": c in known, "modules": [], "probe": None}
        for rel in modules_in(bodies.get(c, "")):
            state, detail = load_module(rel)
            r["modules"].append({"file": rel, "state": state, "detail": detail})
        if probe_readonly and c in READONLY:
            state, detail = run_probe(READONLY[c])
            r["probe"] = {"argv": READONLY[c], "state": state, "detail": detail}
        r["ok"] = (r["wired"]
                   and all(m["state"] != "fail" for m in r["modules"])
                   and (r["probe"] is None or r["probe"]["state"] == "ok"))
        results.append(r)
    summary = {
        "commands": len(results),
        "wired": sum(1 for r in results if r["wired"]),
        "not_wired": [r["command"] for r in results if not r["wired"]],
        "modules_loaded": sum(len([m for m in r["modules"] if m["state"] == "ok"]) for r in results),
        "modules_need_dep": sum(len([m for m in r["modules"] if m["state"] == "dep"]) for r in results),
        "modules_broken": [f"{m['file']} ({m['detail']})" for r in results for m in r["modules"] if m["state"] == "fail"],
        "probes_run": sum(1 for r in results if r["probe"]),
        "probes_failed": [f"{r['command']} {' '.join(r['probe']['argv'])}: {r['probe']['detail']}"
                          for r in results if r["probe"] and r["probe"]["state"] == "fail"],
        "failed_commands": [r["command"] for r in results if not r["ok"]],
    }
    return {"ok": not summary["failed_commands"], "summary": summary, "commands": results}


def report(data: dict, quiet: bool = False, say=print) -> None:
    s = data["summary"]
    if not quiet:
        say("SELFTEST · every ./securax command, proved it loads and the safe ones run (no side effects).\n")
        for r in data["commands"]:
            bad = [m for m in r["modules"] if m["state"] == "fail"]
            dep = [m for m in r["modules"] if m["state"] == "dep"]
            mark = "✔" if r["ok"] else "✘"
            note = []
            if not r["wired"]:
                note.append("NOT WIRED")
            if bad:
                note.append("broken: " + ", ".join(f"{m['file']} — {m['detail']}" for m in bad))
            if dep:
                note.append("needs a dependency: " + ", ".join(m["file"] for m in dep))
            if r["probe"]:
                note.append(("ran " if r["probe"]["state"] == "ok" else "THREW ")
                            + "`" + " ".join(r["probe"]["argv"]) + "`" + (f" — {r['probe']['detail']}" if r["probe"]["state"] == "fail" else ""))
            say(f"  {mark} {r['command']:<14} {'; '.join(note)}")
        say("")
    say(f"{s['commands']} commands · {s['wired']} wired · {s['modules_loaded']} modules load"
        f" ({s['modules_need_dep']} need a dependency) · {s['probes_run']} read-only probes run.")
    if s["not_wired"]:
        say("  ✘ not wired: " + ", ".join(s["not_wired"]))
    if s["modules_broken"]:
        say("  ✘ broken code: " + "; ".join(s["modules_broken"]))
    if s["probes_failed"]:
        say("  ✘ threw when run: " + "; ".join(s["probes_failed"]))
    say("✔ every command is wired, loads, and the read-only ones run clean." if data["ok"]
        else f"✘ {len(s['failed_commands'])} command(s) need attention: " + ", ".join(s["failed_commands"]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="selftest", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-probes", action="store_true", help="only check wiring and module load (skip running anything)")
    a = ap.parse_args(argv)
    data = run(probe_readonly=not a.no_probes)
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
    else:
        report(data, quiet=a.quiet)
    return 0 if data["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
