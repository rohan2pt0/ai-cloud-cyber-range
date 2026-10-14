#!/usr/bin/env python3
"""GAME DAYS — break it on purpose, watch it recover, keep the receipt (Netflix-style chaos, sized for one person).

A resilience claim that has never been tested is a hope. Each scenario injects ONE real failure into the burrow twin (real k3s), then
checks three things: it was DETECTED, the blast radius stayed SMALL, and it RECOVERED within its SLO. The twin is left exactly as it
was found (woken for the drill, put back to sleep after) unless you pass --keep.

    ./securax gameday list
    ./securax gameday run node-loss | control-plane-restart | snapshot-restore
    ./securax gameday all [--out evidence]

The estate's own self-healing (kill a container, watchdog alerts) is exercised by the sandbox journeys `self_healing` and
`watchdog_heals_and_alerts`; this adds the cluster layer and, importantly, a real disaster-recovery drill (etcd snapshot restore).
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import burrow as bw  # noqa: E402


def slo() -> dict:
    return json.loads((HERE / "fitness.json").read_text("utf-8"))["gameday_slo_s"]


def say(m: str = "") -> None:
    print(m, flush=True)


class Run:
    """Records timed steps. A step passes if its check returns truthy within its SLO (seconds)."""

    def __init__(self, name: str) -> None:
        self.name, self.steps, self.t0 = name, [], time.time()

    def step(self, what: str, fn, within: float | None = None, poll: bool = False) -> bool:
        t = time.time()
        ok, note = False, ""
        try:
            if poll:
                end = t + (within or 60)
                while time.time() < end:
                    ok = bool(fn())
                    if ok:
                        break
                    time.sleep(2)
                note = "" if ok else f"not satisfied after {within}s"
            else:
                ok = bool(fn())
        except Exception as e:  # noqa: BLE001 - a drill must report, not crash
            note = f"{type(e).__name__}: {str(e)[:100]}"
        dt = round(time.time() - t, 1)
        if within is not None and dt > within:
            ok, note = False, (note or f"took {dt}s, SLO {within}s")
        self.steps.append({"step": what, "ok": ok, "seconds": dt, "slo": within, "note": note})
        say(f"    {'✔' if ok else '✘'} {what:<58} {dt:>6}s" + (f"  (SLO {within}s)" if within else "") + (f"  {note}" if note and not ok else ""))
        return ok

    def result(self) -> dict:
        return {"scenario": self.name, "ok": all(s["ok"] for s in self.steps), "seconds": round(time.time() - self.t0, 1), "steps": self.steps}


def ready_nodes() -> set[str]:
    return {k for k, v in bw.nodes().items() if v["ready"]}


ALL_NODES = lambda: {n["name"] for n in bw.twin_nodes()}  # noqa: E731


def api_up() -> bool:
    return bw.kubectl("get", "--raw", "/readyz")[0] == 0


def sc_node_loss(r: Run, s: dict) -> None:
    victim = next(n["name"] for n in bw.twin_nodes() if n.get("gpu"))                 # lose the GPU node: the most specialised one
    r.step(f"inject: power off node '{victim}'", lambda: bw.sh(["docker", "stop", "-t", "3", bw.cname(victim)])[0] == 0)
    r.step("detected: the control plane marks it NotReady", lambda: victim not in ready_nodes(), s["node_detect"], poll=True)
    r.step("blast radius: the other nodes stay Ready", lambda: ready_nodes() == ALL_NODES() - {victim})
    r.step("blast radius: the API keeps answering", api_up)
    r.step(f"recover: power '{victim}' back on", lambda: bw.sh(["docker", "start", bw.cname(victim)])[0] == 0)
    r.step("recovered: every node Ready again", lambda: ready_nodes() == ALL_NODES(), s["node_recover"], poll=True)


def sc_control_plane_restart(r: Run, s: dict) -> None:
    r.step("setup: write a marker into the cluster", lambda: bw.kubectl("create", "configmap", "gd-marker", "--from-literal=v=alive")[0] == 0)
    r.step("inject: restart the control plane", lambda: bw.sh(["docker", "restart", "-t", "3", bw.server_name()])[0] == 0)
    r.step("recovered: the API answers again", api_up, s["control_plane_back"], poll=True)
    r.step("data survived: the marker is still there", lambda: bw.kubectl("get", "configmap", "gd-marker", "-o", "jsonpath={.data.v}")[1].strip() == "alive")
    r.step("recovered: every node Ready again", lambda: ready_nodes() == ALL_NODES(), s["node_recover"], poll=True)
    bw.kubectl("delete", "configmap", "gd-marker")


def sc_snapshot_restore(r: Run, s: dict) -> None:
    snap = {"name": ""}
    r.step("setup: write the 'before disaster' marker", lambda: bw.kubectl("create", "configmap", "gd-before", "--from-literal=v=1")[0] == 0)
    r.step("backup: take an etcd snapshot", lambda: bw.sh(["docker", "exec", bw.server_name(), "k3s", "etcd-snapshot", "save", "--name", "gameday"])[0] == 0)
    r.step("disaster: delete the marker, write a rogue one", lambda: bw.kubectl("delete", "configmap", "gd-before")[0] == 0 and bw.kubectl("create", "configmap", "gd-after", "--from-literal=v=2")[0] == 0)
    r.step("stop every node (a cluster cannot be rewound while running)", lambda: all(bw.sh(["docker", "stop", "-t", "5", bw.cname(n["name"])])[0] == 0 for n in sorted(bw.twin_nodes(), key=lambda n: n["role"] == "server")))
    r.step("restore the control plane from the snapshot", lambda: bw.twin_restore(snap.setdefault("name", bw.newest_snapshot())) == 0, s["restore_total"])
    r.step("start the control plane", lambda: bw.sh(["docker", "start", bw.server_name()])[0] == 0)
    r.step("recovered: the API answers again", api_up, s["control_plane_back"], poll=True)
    r.step("data restored: the 'before' marker is back", lambda: bw.kubectl("get", "configmap", "gd-before", "-o", "jsonpath={.data.v}")[1].strip() == "1")
    r.step("rewound: the rogue post-snapshot marker is gone", lambda: bw.kubectl("get", "configmap", "gd-after")[0] != 0)
    r.step("start the agents", lambda: all(bw.sh(["docker", "start", bw.cname(n["name"])])[0] == 0 for n in bw.twin_nodes() if n["role"] == "agent"))
    r.step("recovered: every node Ready again", lambda: ready_nodes() == ALL_NODES(), s["node_recover"], poll=True)
    bw.kubectl("delete", "configmap", "gd-before", "gd-after")


SCENARIOS = {
    "node-loss": ("Power off the GPU node: is it noticed, is the damage contained, does it rejoin?", sc_node_loss),
    "control-plane-restart": ("Restart the control plane: does the API return, does the data survive?", sc_control_plane_restart),
    "snapshot-restore": ("DISASTER RECOVERY DRILL: corrupt the cluster, stop it, restore the etcd snapshot, prove the data is back.", sc_snapshot_restore),
}


def run_scenarios(names: list[str], keep: bool) -> list[dict]:
    prior = bw.twin_status()
    if prior != "awake":
        say(f"(the burrow twin is {prior}: waking it for the drill; it will be put back as found{' unless --keep' if not keep else ''})")
        if bw.twin_up() != 0:
            raise SystemExit("could not wake the burrow twin (is Docker running?)")
    out = []
    try:
        for n in names:
            say(f"\n▶ {n} — {SCENARIOS[n][0]}")
            r = Run(n)
            SCENARIOS[n][1](r, slo())
            res = r.result()
            say(f"  → {'PASS' if res['ok'] else 'FAIL'} in {res['seconds']}s")
            out.append(res)
    finally:
        if not keep:
            if prior == "dormant":
                bw.twin_down()
            elif prior == "hibernating":
                bw.twin_stop()
    return out


def report_md(results: list[dict]) -> str:
    lines = ["# Game day report", "", f"Run {time.strftime('%Y-%m-%d %H:%M:%S')} against the burrow twin (real k3s). Each step lists its SLO.", ""]
    for r in results:
        lines += [f"## {'✅' if r['ok'] else '❌'} {r['scenario']} ({r['seconds']}s)", "", "| step | result | seconds | SLO |", "|---|---|---|---|"]
        lines += [f"| {s['step']} | {'ok' if s['ok'] else 'FAILED ' + s['note']} | {s['seconds']} | {s['slo'] or ''} |" for s in r["steps"]]
        lines.append("")
    lines += ["## What this proves, and what it does not", "- Proves: detection, containment and recovery of the cluster layer on a twin of your future hardware, and a working etcd restore.",
              "- Does **not** prove: real NICs/disks/power, workload-level recovery on a kernel that cannot start pods in k3s-in-Docker, or the estate's compose services (see journeys `self_healing`, `watchdog_heals_and_alerts`)."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("action", choices=["list", "run", "all"])
    ap.add_argument("scenario", nargs="?", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--keep", action="store_true", help="leave the twin awake afterwards")
    a = ap.parse_args()
    if a.action == "list":
        for n, (what, _) in SCENARIOS.items():
            say(f"  {n:<22} {what}")
        return 0
    if a.action == "run" and a.scenario not in SCENARIOS:
        say(f"unknown scenario '{a.scenario}'. Try: ./securax gameday list")
        return 2
    names = list(SCENARIOS) if a.action == "all" else [a.scenario]
    results = run_scenarios(names, a.keep)
    if a.out:
        d = pathlib.Path(a.out)
        d.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        (d / f"gameday-{stamp}.json").write_text(json.dumps(results, indent=2))
        (d / f"gameday-{stamp}.md").write_text(report_md(results))
        say(f"\nreport: {d / f'gameday-{stamp}.md'}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
