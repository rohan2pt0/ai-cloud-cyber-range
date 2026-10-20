#!/usr/bin/env python3
"""The crown jewels of the SecuRAX estate, assessed and ranked automatically (doc 84).

    ./securax jewels             each jewel, how exposed it is today, and the one thing to do next, worst first
    ./securax jewels --json      the same, for the cockpit and the risk register

The jewels are data (governance/jewels.json). Each run checks the estate itself (backups, the key, the code mirror, the keys in
.env, a known working version, the AI rungs, accounts, disk) and turns the result into a risk:
  likelihood = 1 when every check passes, +2 for each check that fails (at most 5); a check that cannot be told adds 1
  score      = impact x likelihood, and x1.5 for a single point of failure (one copy, one machine, one account)
  priority   = DO NOW (score >= 15) · THIS WEEK (8-14) · WATCH (below 8)
So the ranking moves as you fix things, without anyone re-scoring by hand. Standard library only. Exit 0 always (it is a report).
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import stat
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import continuity as ct  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "governance" / "jewels.json"
DAY = 24 * 60


def _age_ok(minutes: float | None, limit: float) -> bool | None:
    return None if minutes is None else minutes <= limit


def checks() -> dict[str, tuple[bool | None, str]]:
    """{check id: (passed? None when it cannot be told, what it found)}."""
    out: dict[str, tuple[bool | None, str]] = {}
    b = ct.rpo_minutes("backup")
    out["backup_recent"] = (bool(b is not None and b <= 26 * 60), "no backup yet" if b is None else f"newest backup {b / 60:.0f} h old")
    out["backup_encrypted"] = (bool(ct.env("SECURAX_BACKUP_KEYFILE")), "backups encrypted" if ct.env("SECURAX_BACKUP_KEYFILE") else "backups are not encrypted")
    o = ct.rpo_minutes("offsite")
    out["offsite_recent"] = (bool(o is not None and o <= 26 * 60), "no off-site copy" if o is None else f"newest off-site copy {o / 60:.0f} h old")
    d = ct.last_drills().get("laptop-lost") or ct.last_drills().get("data-lost") or ct.last_drills().get("backup-key-lost")
    out["offsite_drilled"] = (bool(d and d.get("ok") and time.time() - time.mktime(time.strptime(d["when"][:19], "%Y-%m-%dT%H:%M:%S")) < 100 * 86400),
                              f"last restore drill {d['when'][:10]}" if d else "a restore has never been drilled")
    r = ct.rpo_minutes("repo")
    out["repo_bundle_recent"] = (bool(r is not None and r <= 7 * DAY), "no code bundle yet" if r is None else "code bundle is current" if r == 0 else f"code bundle {r / DAY:.0f} days behind")
    remotes = [x for x in ct.git("remote")[1].split() if x != "origin"]
    out["repo_mirror"] = (bool(ct.env("MIRROR_REMOTES") or remotes), "a second git host is set" if ct.env("MIRROR_REMOTES") or remotes else "only GitHub holds the code")
    key = ct.env("LITELLM_MASTER_KEY")
    out["router_key_changed"] = (None if not ct.ENVF.exists() else bool(key and key != "sk-range-dev" and not key.startswith("sk-change")),
                                 "no .env yet" if not ct.ENVF.exists() else "router key replaced" if key and key != "sk-range-dev" else "router key is the shipped default")
    if ct.ENVF.exists():
        mode = stat.S_IMODE(ct.ENVF.stat().st_mode)
        out["env_private"] = (not (mode & 0o077), ".env readable only by you" if not mode & 0o077 else f".env is readable by others (mode {oct(mode)})")
    else:
        out["env_private"] = (None, "no .env yet")
    good = home_ledger()
    out["known_good"] = (bool(good), f"{good} working version(s) recorded" if good else "no working version recorded yet")
    rungs = live_cloud_rungs()
    out["two_cloud_rungs"] = (None if rungs is None else rungs >= 2, "cannot read the provider settings" if rungs is None else f"{rungs} cloud provider(s) on the build chain")
    out["password_manager"] = (bool(ct.env("PASSWORDS_ENABLED") == "1"), "the estate's password manager is on" if ct.env("PASSWORDS_ENABLED") == "1" else "no password manager in the estate yet")
    free = shutil.disk_usage(str(ROOT)).free / shutil.disk_usage(str(ROOT)).total
    out["disk_free"] = (free >= 0.10, f"{free:.0%} of the disk free")
    return out


def home_ledger() -> int:
    p = pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax") / "known-good.jsonl"
    try:
        return len([x for x in p.read_text("utf-8").splitlines() if x.strip()])
    except OSError:
        return 0


def live_cloud_rungs() -> int | None:
    try:
        sys.path.insert(0, str(ROOT / "local" / "compose"))
        import gen_litellm_config as gen
        e = {**gen.parse_env_file(str(ct.ENVF)), **os.environ}
        cat = gen.load_catalog(gen.CATALOG)
        live = gen.live_chain(gen.chains_for(cat, e).get("builder", []), set(gen.enabled_llm_ids(cat, e)))
        return len([i for i in live if i not in ("home", "coder", "local")])
    except Exception:  # noqa: BLE001 - a report must not fail because one input is unreadable
        return None


def assess(catalogue: dict | None = None, found: dict | None = None) -> list[dict]:
    catalogue = catalogue or json.loads(CATALOGUE.read_text("utf-8"))
    found = found if found is not None else checks()
    rows = []
    for j in catalogue["jewels"]:
        res = [(c, *found.get(c, (None, "not checked"))) for c in j["checks"]]
        fails = sum(2.0 if ok is False else 1.0 if ok is None else 0.0 for _, ok, _ in res)
        likelihood = min(5.0, 1.0 + fails)
        score = round(j["impact"] * likelihood * (1.5 if j.get("spof") else 1.0), 1)
        prio = "DO NOW" if score >= 15 else "THIS WEEK" if score >= 8 else "WATCH"
        rows.append({**{k: j[k] for k in ("id", "name", "why", "impact", "treat", "command", "scenario")}, "spof": bool(j.get("spof")),
                     "likelihood": likelihood, "score": score, "priority": prio,
                     "findings": [{"check": c, "ok": ok, "found": what} for c, ok, what in res]})
    return sorted(rows, key=lambda r: (-r["score"], r["id"]))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    rows = assess()
    if "--json" in argv:
        print(json.dumps({"jewels": rows, "do_now": [r["id"] for r in rows if r["priority"] == "DO NOW"]}, indent=1))
        return 0
    print("CROWN JEWELS · what SecuRAX cannot lose, how exposed each one is today, worst first\n")
    for r in rows:
        print(f"  [{r['priority']:<9}] {r['name']}  (score {r['score']:g}{', single point of failure' if r['spof'] else ''})")
        for f in r["findings"]:
            print(f"      {'✔' if f['ok'] else '?' if f['ok'] is None else '✗'} {f['found']}")
        if r["priority"] != "WATCH" or any(f["ok"] is False for f in r["findings"]):
            print(f"      next: {r['treat']}  →  {r['command']}")
    top = [r for r in rows if r["priority"] == "DO NOW"]
    print(f"\n{len(top)} to do now. If one of these happens anyway, the steps are ready:  ./securax continuity show <scenario>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
