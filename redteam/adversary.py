#!/usr/bin/env python3
"""The adversary ledger: turn every bounty or red-team finding into a permanent regression, and prove it stayed closed.

A bug-bounty program against the AI estate is only worth paying for if each finding becomes the LAST of its kind. This is
the estate's antifragility principle (AGENTS.md) made into a gate: a finding is not "fixed" until it is reproduced as a
probe the purple loop fires every run, a lesson the next builder reads, and (for a class of attack) a drill. `verify`
refuses a closed finding that has no such proof, exactly as the regulator maps refuse a "supported" control with no test.

The raw finding (payload, reporter, severity, fix-by date) lives in the private findings register, kept out of git:
    ./securax findings add "bounty: <paraphrase>" --severity high --asset gateway   # intake, source stays in vault/
This ledger is the PUBLIC learning layer on top: the finding CLASS and its permanent defence, never a secret payload.

    ./securax adversary                      the ledger, newest first, with each finding's permanent regression
    ./securax adversary add --title "..." --class ASI06 --severity high \
                            --probe history-poisoning [--atlas AML.T0080] [--lesson "..."] [--drill ai-incident] \
                            [--source bounty] [--reporter HANDLE] [--reported YYYY-MM-DD] [--fixed YYYY-MM-DD]
    ./securax adversary verify               every finding cites a probe/test that EXISTS; every closed one has one; repeat-class rate is 0 (exit 1 otherwise)
    ./securax adversary status [--json]      the scoreboard the board sees: classes closed, repeat-class rate, days-to-regression

A finding's `regression` is either a purple-loop probe id (--probe, the usual: the probe that got through is promoted to an
attack once the fix lands) or a test reference path::name (--test). Open findings are tracked too: they must already be
reproduced as a probe (a known gap), so nothing is "noted" without being fired. Standard library only; no gateway needed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER = ROOT / "redteam" / "adversary-ledger.json"
# The same risk vocabulary the purple loop uses, so a class here is a class there.
CLASSES = [f"LLM{i:02d}" for i in range(1, 11)] + [f"ASI{i:02d}" for i in range(1, 11)] + ["BIAS", "TOXICITY"]
SEVERITIES = ("critical", "high", "medium", "low")
# Where a probe id may be defined: the purple loop's own probes and the shared attack set it reuses.
PROBE_SOURCES = ("redteam/purple.py", "redteam/run_attacks.py")


def today() -> dt.date:
    return dt.date.today()


def load(path: pathlib.Path | None = None) -> dict:
    try:
        return json.loads((path or LEDGER).read_text("utf-8"))
    except (OSError, ValueError):
        return {"ledger": []}


def save(reg: dict, path: pathlib.Path | None = None) -> None:
    p = path or LEDGER
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n", "utf-8")


def _probe_ids(root: pathlib.Path | None = None) -> set[str]:
    """Every probe/attack id defined in the red-team code, read from source so no gateway import is needed."""
    root = root or ROOT
    ids: set[str] = set()
    for rel in PROBE_SOURCES:
        try:
            text = (root / rel).read_text("utf-8")
        except OSError:
            continue
        ids |= set(re.findall(r'"id":\s*"([A-Za-z0-9-]+)"', text))       # purple.py probe dicts
        ids |= set(re.findall(r'\(\s*"([a-z0-9-]+)",\s*"(?:LLM|ASI)\d', text))  # run_attacks.py ATTACKS tuples
    return ids


def _test_ok(ref: str, root: pathlib.Path | None = None) -> bool:
    """A test reference 'path::name' resolves when the file exists and defines that test."""
    root = root or ROOT
    if "::" not in ref:
        return False
    rel, name = ref.split("::", 1)
    try:
        return bool(re.search(rf"\bdef {re.escape(name.strip())}\b", (root / rel).read_text("utf-8")))
    except OSError:
        return False


def regression_ref(f: dict) -> str:
    reg = f.get("regression") or {}
    return reg.get("probe") and f"probe:{reg['probe']}" or reg.get("test") and f"test:{reg['test']}" or ""


def regression_exists(f: dict, ids: set[str] | None = None, root: pathlib.Path | None = None) -> bool:
    reg = f.get("regression") or {}
    if reg.get("probe"):
        return reg["probe"] in (ids if ids is not None else _probe_ids(root))
    if reg.get("test"):
        return _test_ok(reg["test"], root)
    return False


# A paraphrased title is public; a raw payload is not. Refuse what the PII/secret gate would flag, so the ledger stays shippable.
_LOOKS_SECRET = re.compile(r"(?:\d[ -]?){13,19}|\b(AKIA|ASIA)[A-Z0-9]{16}\b|\bghp_[A-Za-z0-9]{20,}\b"
                           r"|\b[\w.+-]+@(?!example\.|evil\.example)[\w-]+\.[\w.-]+\b")


def problems(reg: dict, ids: set[str] | None = None, root: pathlib.Path | None = None) -> list[str]:
    ids = ids if ids is not None else _probe_ids(root)
    out: list[str] = []
    seen_ids: set[str] = set()
    for f in reg.get("ledger", []):
        fid = f.get("id", "?")
        if fid in seen_ids:
            out.append(f"{fid}: duplicate id")
        seen_ids.add(fid)
        if f.get("class") not in CLASSES:
            out.append(f"{fid}: unknown class '{f.get('class')}' (use one of the OWASP LLM/Agentic ids, BIAS or TOXICITY)")
        if f.get("severity") not in SEVERITIES:
            out.append(f"{fid}: severity must be {SEVERITIES}")
        if _LOOKS_SECRET.search(f.get("title", "")):
            out.append(f"{fid}: the title looks like it carries a payload/secret/PII — paraphrase it (the raw finding goes in vault/ via ./securax findings)")
        if not regression_ref(f):
            out.append(f"{fid}: no regression — every adversary finding must be reproduced as a purple probe (--probe) or a test (--test), fixed or not")
        elif not regression_exists(f, ids, root):
            out.append(f"{fid}: regression {regression_ref(f)} does not exist in the red-team code (the claim is stale)")
        if f.get("fixed") and not f.get("lesson"):
            out.append(f"{fid}: a closed finding must carry the lesson the next builder reads (--lesson)")
    out += [f"repeat-class: {c}" for c in repeat_classes(reg)]
    return out


def repeat_classes(reg: dict) -> list[str]:
    """A class that recurred AFTER it was closed: the loop failed to make the fix permanent. This must stay empty."""
    by: dict[str, list[dict]] = {}
    for f in reg.get("ledger", []):
        by.setdefault(f.get("class", "?"), []).append(f)
    bad = []
    for cls, items in by.items():
        closed = [dt.date.fromisoformat(f["fixed"]) for f in items if f.get("fixed")]
        later = [dt.date.fromisoformat(f["reported"]) for f in items if f.get("reported")]
        if closed and any(r > min(closed) for r in later):
            bad.append(cls)
    return sorted(bad)


def status(reg: dict, root: pathlib.Path | None = None) -> dict:
    ids = _probe_ids(root)
    items = reg.get("ledger", [])
    closed = [f for f in items if f.get("fixed")]
    days = sorted((dt.date.fromisoformat(f["fixed"]) - dt.date.fromisoformat(f["reported"])).days
                  for f in closed if f.get("reported") and f.get("fixed"))
    return {"findings": len(items), "closed": len(closed), "open": len(items) - len(closed),
            "reproduced": sum(1 for f in items if regression_exists(f, ids, root)),
            "classes_covered": sorted({f["class"] for f in items if f.get("class") in CLASSES}),
            "repeat_classes": repeat_classes(reg),
            "median_days_to_regression": days[len(days) // 2] if days else None,
            "sources": sorted({f.get("source", "internal-redteam") for f in items})}


def recent_closed(reg: dict, now: dt.date | None = None, days: int = 30) -> int:
    """Closed-with-a-living-regression in the window — the number `./securax progress` shows as estate hardening."""
    now, ids = now or today(), _probe_ids()
    cut = now - dt.timedelta(days=days)
    return sum(1 for f in reg.get("ledger", [])
               if f.get("fixed") and dt.date.fromisoformat(f["fixed"]) >= cut and regression_exists(f, ids))


def _next_id(reg: dict) -> str:
    nums = [int(m.group(1)) for f in reg.get("ledger", []) if (m := re.match(r"ADV-(\d+)$", f.get("id", "")))]
    return f"ADV-{(max(nums) + 1) if nums else 1:04d}"


def add(reg: dict, args: argparse.Namespace) -> dict:
    if not (args.probe or args.test):
        raise ValueError("A finding needs its regression: --probe <purple-probe-id> or --test path::name")
    f = {"id": args.id or _next_id(reg), "title": args.title.strip(), "class": args.klass.upper(),
         "atlas": args.atlas or None, "severity": args.severity.lower(), "source": args.source,
         "reporter": (args.reporter or "").strip(), "reported": args.reported or today().isoformat(),
         "fixed": args.fixed or None,
         "regression": {"probe": args.probe} if args.probe else {"test": args.test},
         "lesson": (args.lesson or "").strip(), "drill": (args.drill or "").strip()}
    reg.setdefault("ledger", []).append(f)
    bad = problems(reg)
    if any(f["id"] in p for p in bad):
        reg["ledger"].pop()
        raise ValueError("Refused — " + "; ".join(p for p in bad if f["id"] in p))
    return f


def _line(f: dict) -> str:
    st = "✔ closed" if f.get("fixed") else "○ open"
    reg = regression_ref(f).replace("probe:", "purple ").replace("test:", "test ")
    return (f"  {f['id']}  {st:<9} {f['severity']:<8} {f['class']:<8} {f['title'][:64]}\n"
            f"        regression: {reg}" + (f" · drill {f['drill']}" if f.get('drill') else "")
            + (f" · {f['source']}" if f.get('source') and f['source'] != 'internal-redteam' else ""))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog="./securax adversary", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("add")
    p.add_argument("--title", required=True)
    p.add_argument("--class", dest="klass", required=True)
    p.add_argument("--severity", required=True)
    p.add_argument("--atlas", default="")
    p.add_argument("--probe", default="")
    p.add_argument("--test", default="")
    p.add_argument("--lesson", default="")
    p.add_argument("--drill", default="")
    p.add_argument("--source", default="bounty")
    p.add_argument("--reporter", default="")
    p.add_argument("--reported", default="")
    p.add_argument("--fixed", default="")
    p.add_argument("--id", default="")
    sub.add_parser("list")
    sub.add_parser("verify")
    s = sub.add_parser("status")
    s.add_argument("--json", action="store_true")
    a = ap.parse_args(argv or ["list"])
    reg = load()
    try:
        if a.cmd == "add":
            f = add(reg, a)
            save(reg)
            print(f"✔ {f['id']} recorded ({f['class']}, {f['severity']}). Regression: {regression_ref(f)}.")
            print("  Run ./securax adversary verify to prove it fires, and ./securax purple to see it held.")
            return 0
        if a.cmd == "verify":
            bad = problems(reg)
            if bad:
                print(f"✗ {len(bad)} problem(s) — a finding is not closed until its regression is real:")
                for b in bad:
                    print("  - " + b)
                return 1
            s = status(reg)
            print(f"✔ adversary ledger consistent: {s['closed']}/{s['findings']} closed, every finding reproduced, repeat-class rate 0.")
            return 0
        if a.cmd == "status":
            s = status(reg)
            if a.json:
                print(json.dumps(s, indent=2))
                return 0
            print("Adversary ledger — what the bounty program taught the estate")
            print(f"  findings: {s['findings']}  ·  closed: {s['closed']}  ·  open: {s['open']}  ·  reproduced as a probe/test: {s['reproduced']}/{s['findings']}")
            print(f"  repeat-class rate: {len(s['repeat_classes'])}" + (f" ({', '.join(s['repeat_classes'])})" if s['repeat_classes'] else " (no class has recurred after it was closed)"))
            if s["median_days_to_regression"] is not None:
                print(f"  median days from report to permanent regression: {s['median_days_to_regression']}")
            print(f"  classes with a finding: {', '.join(s['classes_covered']) or 'none yet'}")
            print(f"  sources: {', '.join(s['sources']) or 'none yet'}")
            return 0
        items = sorted(reg.get("ledger", []), key=lambda f: (f.get("reported", ""), f.get("id", "")), reverse=True)
        if not items:
            print("The adversary ledger is empty. Record a finding once it is reproduced as a purple probe:\n"
                  "  ./securax adversary add --title \"...\" --class LLM01 --severity high --probe <probe-id>")
            return 0
        print(f"Adversary ledger — {len(items)} finding(s), each reproduced so it cannot come back unseen:\n")
        for f in items:
            print(_line(f))
        return 0
    except (KeyError, ValueError) as e:
        print(str(e).strip("'\""))
        return 1


if __name__ == "__main__":
    sys.exit(main())
