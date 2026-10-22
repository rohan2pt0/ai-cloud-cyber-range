#!/usr/bin/env python3
"""Chaos experiments on the everyday estate (doc 101), the way the Principles of Chaos Engineering and Google's DiRT do it:
state the normal behaviour, break one real thing, check the estate returns to normal within a time limit, and ALWAYS put
the thing back. The seed picks the faults, so any failure can be replayed exactly.

    ./securax chaos                     the plan only: which faults, in what order (changes nothing)
    ./securax chaos --run               run it on THIS machine: services break for up to a minute each
    ./securax chaos --seed 20261022 --faults 3 --run
    ./securax chaos --json

Normal behaviour (the steady state): the AI gateway is ready, a chat question gets an answer, the Command Center page
serves, and the sync service answers. An experiment never starts on an estate that is already not normal.

Recovery is what the estate promises a person: the watchdog (`./securax watch --once`) heals within its interval.
Standard library and the docker CLI only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import random
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "local" / "compose"
GATEWAY = "http://127.0.0.1:8080"
HUB = "http://127.0.0.1:8088"


# ----------------------------------------------------------------------------------------------------------- the catalog
# Each fault: what breaks, how it is put back, and how long the estate may take to be normal again.
CATALOG = {
    "kill-gateway": {"what": "the AI gateway stops (a crash)", "service": "gateway", "inject": ["kill"], "revert": ["start"], "slo_s": 180},
    "kill-router": {"what": "the model router stops mid-traffic", "service": "litellm", "inject": ["kill"], "revert": ["start"], "slo_s": 240},
    "kill-hub": {"what": "the Command Center's web server stops", "service": "guiding-map", "inject": ["kill"], "revert": ["start"], "slo_s": 180},
    "kill-sync": {"what": "the sync service stops", "service": "estate-sync", "inject": ["kill"], "revert": ["start"], "slo_s": 180},
    "hang-gateway": {"what": "the AI gateway hangs (frozen, not dead)", "service": "gateway", "inject": ["pause"], "revert": ["unpause"], "slo_s": 240},
}


def plan(seed: int, n: int, catalog: dict | None = None) -> list[str]:
    """The faults for this seed, in order: the same seed always gives the same plan."""
    names = sorted(catalog or CATALOG)
    return random.Random(seed).sample(names, min(n, len(names)))


# ------------------------------------------------------------------------------------------------- the real-world parts
def _get(url: str, timeout: float = 5, data: bytes | None = None) -> bool:
    try:
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 300
    except Exception:  # noqa: BLE001 - any failure is "not normal", which is what is being measured
        return False


def steady_state() -> dict:
    """Is the estate normal? Every part a person relies on, each a yes or no."""
    ask = json.dumps({"model": "bank-assistant", "messages": [{"role": "user", "content": "Reply with: ok"}], "max_tokens": 5}).encode()
    return {"gateway ready": _get(f"{GATEWAY}/readyz"),
            "chat answers": _get(f"{GATEWAY}/v1/chat/completions", 60, ask),
            "Command Center serves": _get(f"{HUB}/hub.html"),
            "sync answers": _get(f"{HUB}/sync/healthz")}


def docker(args: list[str], service: str) -> int:
    """Run one docker action on the estate's container for SERVICE ('kill', 'start', 'pause', or 'exec ...')."""
    cid = subprocess.run(["docker", "compose", "--profile", "ai", "ps", "-aq", service], cwd=COMPOSE,
                         capture_output=True, text=True).stdout.strip().splitlines()
    if not cid:
        return 1
    verb, rest = args[0], args[1:]
    return subprocess.run(["docker", verb, cid[0], *rest], capture_output=True).returncode


def heal() -> None:
    """What the estate promises a person: the watchdog checks once and heals."""
    subprocess.run(["bash", str(ROOT / "securax"), "watch", "--once"], capture_output=True, timeout=900)


# ----------------------------------------------------------------------------------------------------------- the runner
def run(seed: int, n: int, measure=steady_state, act=docker, recover=heal, clock=time.monotonic, sleep=time.sleep,
        catalog: dict | None = None, settle_s: float = 5) -> dict:
    """Run the plan for SEED. Never starts on an estate that is not normal; always reverts each fault."""
    cat = catalog or CATALOG
    out = {"seed": seed, "plan": plan(seed, n, cat), "results": [], "aborted": ""}
    before = measure()
    if not all(before.values()):
        out["aborted"] = "the estate was not normal before the experiment: " + ", ".join(k for k, v in before.items() if not v)
        return out
    for name in out["plan"]:
        f = cat[name]
        t0, ok, why, broken = clock(), False, "", {}
        try:
            act(f["inject"], f["service"])
            sleep(settle_s)
            broken = measure()
            recover()
            while clock() - t0 < f["slo_s"]:
                now = measure()
                if all(now.values()):
                    ok = True
                    break
                sleep(5)
            if not ok:
                why = "still not normal: " + ", ".join(k for k, v in measure().items() if not v)
        except Exception as e:  # noqa: BLE001 - a broken check is a failed experiment, never a left-over fault
            why = f"the check itself failed: {e}"
        finally:
            act(f["revert"], f["service"])
        out["results"].append({"fault": name, "what": f["what"], "ok": ok, "seconds": round(clock() - t0, 1), "slo_s": f["slo_s"],
                               "noticed": bool(broken) and not all(broken.values()), "why": why})
        if not ok:
            break                       # DiRT: when the fix is not quick, stop; do not stack a second fault on a broken estate
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="securax chaos", description=__doc__.split("\n\n")[0])
    ap.add_argument("--seed", type=int, default=int(dt.date.today().strftime("%Y%m%d")))
    ap.add_argument("--faults", type=int, default=3)
    ap.add_argument("--run", action="store_true", help="really break things on this machine (default: show the plan only)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not a.run:
        p = plan(a.seed, a.faults)
        if a.json:
            print(json.dumps({"seed": a.seed, "plan": p}))
        else:
            print(f"Chaos plan for seed {a.seed} (nothing is changed):")
            for name in p:
                print(f"  - {CATALOG[name]['what']}  (must be normal again within {CATALOG[name]['slo_s']} s)")
            print("To run it on this machine (services break for up to a few minutes each):  ./securax chaos --run"
                  + ("" if a.seed == int(dt.date.today().strftime("%Y%m%d")) else f" --seed {a.seed}"))
        return 0
    res = run(a.seed, a.faults)
    if a.json:
        print(json.dumps(res, indent=1))
    else:
        print(f"Chaos seed {res['seed']}" + (f": not started, {res['aborted']}" if res["aborted"] else ""))
        for r in res["results"]:
            print(f"  {'✔' if r['ok'] else '✘'} {r['what']}: normal again in {r['seconds']} s (limit {r['slo_s']} s) {r['why']}")
    return 0 if not res["aborted"] and all(r["ok"] for r in res["results"]) else 1


if __name__ == "__main__":
    sys.exit(main())
