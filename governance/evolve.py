#!/usr/bin/env python3
"""`./securax evolve` — the estate's growth map: what runs as an amoeba, what is ready to grow, and the one step (doc 128).

The `amoeba` principle: ship the simplest living thing that helps today — one person, no server, offline — but carry the
DNA to become the enterprise organism, and build the dormant rail so it can. This reads the estate's own conditions
(how many nodes are live, whether a gateway or a fleet server or an internal mirror or more than one team is present,
and stress signals) and, for each declared capability, shows the stage it is in, whether conditions now favour the next
stage, and the exact rail to pull — doing the safe, in-box steps itself and leaving anything that provisions, costs or
touches endpoints behind ./securax approve. Nature is the architect: a cell becomes an organism only as conditions call.

  ./securax evolve                      the growth map: every capability, its stage, and what is ready to grow now
  ./securax evolve <capability>         the full growth path of one capability (stages, triggers, the rail each needs)
  ./securax evolve --json               the map as data
  ./securax evolve --conditions         just the conditions the estate senses right now

Conditions are read locally — nothing leaves the box. The growth map is DATA (governance/evolution.json); every
enterprise-capable feature should declare its rail there (fitness evolution-declared ratchets the count up, never down).
Standard library only. Growing a form never happens silently: a consequential step is always proposed, never performed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
LIB = HERE / "evolution.json"


def lib() -> dict:
    return json.loads(LIB.read_text("utf-8"))


def _node_count() -> int:
    """How many reference/sync nodes the estate knows — 1 is a lone amoeba. Best-effort, local, never fails the command."""
    try:
        spec = importlib.util.spec_from_file_location("resilience", HERE / "resilience.py")
        res = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(res)
        m = res.model()
        cards = m.get("reference", {}).get("cards", [])
        return max(1, len(cards))
    except Exception:  # noqa: BLE001
        return 1


def conditions() -> dict:
    """What the estate senses about itself, right now, locally."""
    nodes = _node_count()
    return {
        "nodes": nodes,
        "gateway": bool(os.getenv("GATEWAY_URL")),
        "fleet_server": bool(os.getenv("VELOCIRAPTOR_SERVER") or os.getenv("SECURAX_FLEET_SERVER")),
        "internal_mirror": bool(os.getenv("SECURAX_HUNT_MIRROR")),
        "teams": bool(os.getenv("SECURAX_TEAMS") or os.getenv("SECURAX_TENANTS")),
        "load": bool(os.getenv("SECURAX_LOAD_HIGH")),
        "lost_node": bool(os.getenv("SECURAX_NODE_LOST")),
    }


def _met(token: str, cond: dict) -> bool:
    """Evaluate one trigger token against the conditions. Supports `key`, `key>N` and `nodes>N`."""
    token = token.strip()
    if ">" in token:
        key, _, num = token.partition(">")
        key, num = key.strip(), num.strip()
        try:
            return float(cond.get(key, 0) or 0) > float(num)
        except (TypeError, ValueError):
            return False
    return bool(cond.get(token))


def _stage_now(cap: dict, cond: dict) -> int:
    """Index of the highest stage whose conditions are met (0 = amoeba, always 'have')."""
    idx = 0
    for i, st in enumerate(cap["stages"]):
        if i == 0:
            continue
        when = st.get("when", [])
        if when and all(_met(w, cond) for w in when):
            idx = i
    return idx


def _next_ready(cap: dict, cond: dict) -> dict | None:
    """The next stage up from the amoeba whose conditions are now met but which is not the baseline stage — i.e. ready to grow."""
    for i, st in enumerate(cap["stages"]):
        if i == 0:
            continue
        when = st.get("when", [])
        if when and all(_met(w, cond) for w in when):
            return {"index": i, **st}
    return None


def cmd_map(a, cond: dict) -> int:
    data = lib()
    caps = data["capabilities"]
    print("▶ The estate's growth map (principle: start as an amoeba, carry the DNA)\n")
    _print_conditions(cond, short=True)
    print()
    ready = 0
    for cid, cap in caps.items():
        nxt = _next_ready(cap, cond)
        here = cap["stages"][_stage_now(cap, cond)]
        if nxt:
            ready += 1
            how = "the estate can grow it" if nxt.get("actuation") == "auto" else "needs your approval (it provisions / costs / touches endpoints)"
            print(f"  ⇧ {cid:<10} amoeba → {nxt['id']}: conditions favour growing.  {how}")
            print(f"       grows to: {nxt.get('grows_to', '')}")
            print(f"       rail (already built): {nxt.get('rail', '')}")
            print(f"       see:  ./securax evolve {cid}")
        else:
            print(f"  · {cid:<10} {here['id']}: right-sized for now — nothing to grow (this is good)")
    print()
    if ready:
        print(f"{ready} capability(ies) are ready to grow. The estate grows the safe, in-box steps itself; anything that")
        print("provisions, costs or touches an endpoint is proposed for your ./securax approve, never done silently.")
    else:
        print("Everything is right-sized for today's conditions. The organism grows only when conditions call for it.")
    return 0


def _print_conditions(cond: dict, short: bool = False) -> None:
    bits = [f"nodes={cond['nodes']}",
            "gateway" + ("✓" if cond["gateway"] else "✗"),
            "fleet-server" + ("✓" if cond["fleet_server"] else "✗"),
            "mirror" + ("✓" if cond["internal_mirror"] else "✗"),
            "multi-team" + ("✓" if cond["teams"] else "✗")]
    print("  conditions sensed: " + "  ".join(bits))
    if not short:
        print("  stress signals: load " + ("HIGH" if cond["load"] else "normal")
              + ", lost-node " + ("YES → run in amoeba (no-server) mode" if cond["lost_node"] else "no"))


def cmd_conditions(a, cond: dict) -> int:
    print("▶ Conditions the estate senses right now (local, nothing leaves the box):\n")
    _print_conditions(cond, short=False)
    print("\n  Set a signal to let the estate see a change, e.g. SECURAX_HUNT_MIRROR=<url>, GATEWAY_URL=<url>,")
    print("  SECURAX_TEAMS=1, SECURAX_FLEET_SERVER=<addr>. Node count comes from the resilience reference estate.")
    return 0


def cmd_one(a, cond: dict) -> int:
    data = lib()
    cap = data["capabilities"].get(a.capability)
    if not cap:
        print(f"no capability {a.capability!r} in the growth map; known: {', '.join(data['capabilities'])}")
        return 2
    here = _stage_now(cap, cond)
    print(f"▶ {a.capability} — growth path  (amoeba form: {cap['organism']})\n")
    for i, st in enumerate(cap["stages"]):
        mark = "●" if i == here else ("○" if i < here else "◍")
        tag = "YOU ARE HERE" if i == here else ("have" if st.get("have") else "")
        when = st.get("when", [])
        met = (not when) or all(_met(w, cond) for w in when)
        cond_str = "" if not when else ("  [conditions " + ("MET" if met else "not yet") + ": " + ", ".join(when) + "]")
        print(f"  {mark} {st['id']}  {tag}{cond_str}")
        if st.get("is"):
            print(f"       is: {st['is']}")
        if st.get("grows_to"):
            print(f"       grows to: {st['grows_to']}")
        if st.get("rail"):
            print(f"       rail (already built, dormant): {st['rail']}")
        if st.get("actuation"):
            how = "safe, in-box — the estate can do it" if st["actuation"] == "auto" else "behind ./securax approve (provisions / costs / touches endpoints)"
            print(f"       actuation: {how}")
    if cap.get("unfavourable"):
        print("\n  Under stress (antifragile):")
        for k, v in cap["unfavourable"].items():
            print(f"       {k}: {v}")
    nxt = _next_ready(cap, cond)
    if nxt and nxt["index"] != here:
        print(f"\n  ⇧ Ready to grow to '{nxt['id']}'. Pull the rail:  {nxt.get('rail', '')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="evolve", description=__doc__.split("\n\n")[0])
    ap.add_argument("capability", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--conditions", action="store_true")
    a = ap.parse_args(argv)
    cond = conditions()
    if a.json:
        print(json.dumps({"conditions": cond, "map": lib()}, indent=2))
        return 0
    if a.conditions:
        return cmd_conditions(a, cond)
    if a.capability:
        return cmd_one(a, cond)
    return cmd_map(a, cond)


if __name__ == "__main__":
    sys.exit(main())
