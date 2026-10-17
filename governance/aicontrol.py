#!/usr/bin/env python3
"""Human-in-command for AI (RBI draft Model Risk Management guidance, June 2026): stop and resume models, and keep the inventory.

    ./securax ai status                         what is stopped, by whom, since when, and why
    ./securax ai stop all|MODEL --reason "..."  the gateway refuses it on the next request (no restart); the reason is required
    ./securax ai resume all|MODEL               switch it back on
    ./securax ai inventory                      the model inventory: tier, owner, third party, explainability, validation due,
                                                decommissioned models and how long their records are kept
    ./securax ai budget                         each caller's AI allowance: used today / this month, and what is left
    ./securax ai budget extend --day|--month --tokens N --reason "..." [--caller ID]
                                                more tokens for today or this month (everyone, or one caller); logged

The switch is local/compose/controls/ai-control.json, mounted read-only into the gateway (apps/llm-gateway/app/killswitch.py).
Every stop and resume is appended to vault/ai-control-log.jsonl, which is never committed and never trimmed: the draft expects
records to outlive the model. Standard library only (the inventory needs PyYAML, which the estate already uses).
"""
from __future__ import annotations

import datetime as dt
import getpass
import json
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CTL = ROOT / "local" / "compose" / "controls" / "ai-control.json"
LOG = ROOT / "vault" / "ai-control-log.jsonl"
REGISTRY = ROOT / "governance" / "model-registry.yaml"
REVALIDATE_MONTHS = {"high": 12, "limited": 24, "minimal": 36}     # a high-risk model is re-validated at least yearly
RETAIN_YEARS = 10


def read(path: pathlib.Path = CTL) -> dict:
    try:
        return json.loads(path.read_text("utf-8") or "{}")
    except FileNotFoundError:
        return {"all": None, "models": {}}


def write(data: dict, path: pathlib.Path = CTL) -> None:
    """Atomic: the gateway never reads a half-written file (which it would treat as 'stop all')."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".ai-control.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    os.chmod(tmp, 0o644)                   # the gateway runs as another user and must be able to read it
    os.replace(tmp, path)


def log(action: str, scope: str, reason: str, by: str, path: pathlib.Path = LOG) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": dt.datetime.now().isoformat(timespec="seconds"), "action": action, "scope": scope,
                            "reason": reason, "by": by}) + "\n")


def stop(scope: str, reason: str, by: str, path: pathlib.Path = CTL, logp: pathlib.Path = LOG) -> dict:
    if not reason.strip():
        raise SystemExit("A reason is required: it is shown to every caller and kept in the record.  --reason \"...\"")
    d = read(path)
    rec = {"by": by, "at": dt.datetime.now().isoformat(timespec="seconds"), "reason": reason.strip()}
    if scope == "all":
        d["all"] = rec
    else:
        d.setdefault("models", {})[scope] = rec
    write(d, path)
    log("stop", scope, reason, by, logp)
    return d


def resume(scope: str, by: str, path: pathlib.Path = CTL, logp: pathlib.Path = LOG) -> dict:
    d = read(path)
    if scope == "all":
        d["all"] = None
    else:
        d.setdefault("models", {}).pop(scope, None)
    write(d, path)
    log("resume", scope, "", by, logp)
    return d


def extend(period: str, tokens: int, reason: str, by: str, caller: str = "*", today: dt.date | None = None,
           path: pathlib.Path = CTL, logp: pathlib.Path = LOG) -> dict:
    """An extension is for the CURRENT day or month only: a one-off 'extra credit', never a silent new default."""
    if period not in ("day", "month"):
        raise SystemExit("--day or --month")
    if tokens <= 0:
        raise SystemExit("--tokens must be a positive number")
    if not reason.strip():
        raise SystemExit("A reason is required: it is kept in the record.  --reason \"...\"")
    today = today or dt.date.today()
    d = read(path)
    d.setdefault("budget_extensions", []).append({"period": period, "for": today.isoformat() if period == "day" else today.strftime("%Y-%m"),
                                                  "tokens": tokens, "caller": caller, "by": by, "reason": reason.strip()})
    # keep only extensions that can still apply (today's and this month's); older ones stay in the log
    d["budget_extensions"] = [e for e in d["budget_extensions"] if e["for"] in (today.isoformat(), today.strftime("%Y-%m"))]
    write(d, path)
    log(f"budget-extend-{period}", caller, f"+{tokens} tokens: {reason.strip()}", by, logp)
    return d


def _arg(argv: list[str], flag: str, default: str = "") -> str:
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else default


def inventory(today: dt.date | None = None, registry: pathlib.Path = REGISTRY) -> list[dict]:
    import yaml

    today = today or dt.date.today()
    reg = yaml.safe_load(registry.read_text("utf-8")) or {}
    out = []
    for m in reg.get("models", []):
        tier = m.get("risk_tier", "")
        due = ""
        if m.get("validated"):
            v = dt.date.fromisoformat(str(m["validated"]))
            months = REVALIDATE_MONTHS.get(tier, 12)
            y, mo = divmod(v.month - 1 + months, 12)
            due = dt.date(v.year + y, mo + 1, min(v.day, 28)).isoformat()
        problems = [p for p, bad in (("not validated", not m.get("validated")), ("re-validation overdue", bool(due) and due < today.isoformat()),
                                     ("no explainability statement", tier == "high" and not m.get("explainability")),
                                     ("not approved", not m.get("approved"))) if bad]
        out.append({"id": m.get("id"), "tier": tier, "owner": m.get("owner", ""), "third_party": bool(m.get("third_party")),
                    "validated": str(m.get("validated", "")), "revalidate_by": due, "problems": problems})
    for m in reg.get("decommissioned", []) or []:
        end = dt.date.fromisoformat(str(m.get("decommissioned")))
        out.append({"id": m.get("id"), "tier": m.get("risk_tier", ""), "decommissioned": end.isoformat(),
                    "retain_until": end.replace(year=end.year + RETAIN_YEARS).isoformat(), "problems": []})
    return out


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "status"
    by = os.getenv("SECURAX_OPERATOR") or getpass.getuser()
    if cmd in ("stop", "resume"):
        if len(argv) < 2:
            print(f"which model?  ./securax ai {cmd} all|MODEL" + (' --reason "..."' if cmd == "stop" else ""))
            return 2
        scope = argv[1]
        if cmd == "stop":
            reason = argv[argv.index("--reason") + 1] if "--reason" in argv and argv.index("--reason") + 1 < len(argv) else ""
            stop(scope, reason, by)
            print(f"✔ {'ALL AI' if scope == 'all' else scope} stopped. The gateway refuses it from the next request; callers see your reason.")
        else:
            resume(scope, by)
            print(f"✔ {'all AI' if scope == 'all' else scope} switched back on.")
        print(f"  recorded in {LOG.relative_to(ROOT)}")
        return 0
    if cmd == "status":
        d = read()
        if d.get("all"):
            print(f"⛔ ALL AI stopped by {d['all'].get('by')} at {d['all'].get('at')}: {d['all'].get('reason')}")
        for k, v in (d.get("models") or {}).items():
            print(f"⛔ {k} stopped by {v.get('by')} at {v.get('at')}: {v.get('reason')}")
        if not d.get("all") and not d.get("models"):
            print("✔ nothing is stopped")
        return 0
    if cmd == "budget":
        if len(argv) > 1 and argv[1] == "extend":
            period = "day" if "--day" in argv else "month" if "--month" in argv else ""
            try:
                tokens = int(_arg(argv, "--tokens", "0").replace(",", "").replace("_", ""))
            except ValueError:
                tokens = 0
            extend(period, tokens, _arg(argv, "--reason"), by, _arg(argv, "--caller", "*"))
            print(f"✔ +{tokens:,} tokens for {'today' if period == 'day' else 'this month'}"
                  f" ({'every caller' if _arg(argv, '--caller', '*') == '*' else _arg(argv, '--caller')}). The gateway applies it on the next request.")
            print(f"  recorded in {LOG.relative_to(ROOT)}")
            return 0
        try:                                   # ./securax pipes the gateway's /v1/budget here (it knows the address and TLS)
            rep = json.loads(sys.stdin.read() or "{}")
            rep["callers"]
        except (ValueError, KeyError):
            print("Cannot read the allowance from the gateway. Is the estate running?  ./securax up"
                  "   (with sign-in on, set SECURAX_GATEWAY_KEY to an auditor key)")
            return 1
        fmt = lambda u, lim: f"{u:>11,} of {lim:,}" if lim else f"{u:>11,} (no limit)"
        print(f"Allowance per caller: {rep['day_limit']:,} tokens a day, {rep['month_limit']:,} a month "
              f"(warning at {int(rep['warn_at'] * 100)}%; {'local model counted' if rep['count_local'] else 'cloud models only'})")
        for r in rep["callers"]:
            pct = max((r["day_used"] / r["day_limit"]) if r["day_limit"] else 0, (r["month_used"] / r["month_limit"]) if r["month_limit"] else 0)
            mark = "⛔" if pct >= 1 else "⚠" if pct >= rep["warn_at"] else "✔"
            print(f"{mark} caller {r['caller']}  today {fmt(r['day_used'], r['day_limit'])}   month {fmt(r['month_used'], r['month_limit'])}")
        if not rep["callers"]:
            print("✔ nothing spent yet this month")
        return 0
    if cmd == "inventory":
        rows = inventory()
        for r in rows:
            if r.get("decommissioned"):
                print(f"  {r['id']:<26} decommissioned {r['decommissioned']}; records kept until {r['retain_until']}")
            else:
                print(f"{'✗' if r['problems'] else '✔'} {r['id']:<26} {r['tier']:<8} owner {r['owner'] or '-':<22} "
                      f"{'third party ' if r['third_party'] else ''}re-validate by {r['revalidate_by'] or '-'}"
                      + (f"   → {', '.join(r['problems'])}" if r["problems"] else ""))
        return 1 if any(r["problems"] for r in rows) else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
