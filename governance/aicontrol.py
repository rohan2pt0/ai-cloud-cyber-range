#!/usr/bin/env python3
"""Human-in-command for AI (RBI draft Model Risk Management guidance, June 2026): stop and resume models, and keep the inventory.

    ./securax ai status                         what is stopped, by whom, since when, and why
    ./securax ai stop all|MODEL --reason "..."  the gateway refuses it on the next request (no restart); the reason is required
    ./securax ai resume all|MODEL               switch it back on
    ./securax ai inventory                      the model inventory: tier, owner, third party, explainability, validation due,
                                                decommissioned models and how long their records are kept

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
