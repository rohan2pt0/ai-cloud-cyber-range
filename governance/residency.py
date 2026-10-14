#!/usr/bin/env python3
"""Data residency: which data may be processed where — in the gateway (which model sees it) and in the lifecycle (which cloud region wakes).

    ./securax residency status                                  what is enforced, and the zone of every model alias in the router
    ./securax residency enable --jurisdiction IN [--action reroute|block] [--monitor]
    ./securax residency disable
    ./securax residency check --class regulatory --model bank-assistant       what the gateway would do with that
    ./securax residency region aws ap-south-1                   would the lifecycle be allowed to wake a stage there?
    ./securax residency attest aws --ref "MeitY empanelment cert / audit report id or URL" [--by NAME]

The rules are DATA (governance/residency/<JURISDICTION>.json; copy TEMPLATE.example.json for another country or sector), so this serves any
regulated entity: India ships ready (SEBI CSCRF 'Regulatory Data' stays in India; RBI/DPDP expectations alike); other jurisdictions are
a file. Zones: `local` = your machine/LAN, a named in-country zone for clouds you have attested, `global` = anywhere. A model with no
zone is `global`. Honest limits: the gateway can only judge what it can see (patterns such as Aadhaar/PAN/card numbers, the caller's
default class, and the X-Data-Class header) - it cannot know that free text is confidential; and it cannot verify a cloud's
empanelment: `attest` records YOUR evidence reference and the lifecycle refuses to wake an unattested cloud when residency is enforced.
Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
ENV = ROOT / "local" / "compose" / ".env"
POLICIES = HERE / "residency"
ATTEST = pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax") / "residency-attestations.json"


def _mod(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def gw():
    return _mod("securax_residency_rt", "apps/llm-gateway/app/residency.py")


def read_env(path: pathlib.Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if path.exists():
        for ln in path.read_text("utf-8").splitlines():
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip("'\"")
    return out


def set_env(path: pathlib.Path, key: str, value: str) -> None:
    lines = path.read_text("utf-8").splitlines() if path.exists() else []
    for i, ln in enumerate(lines):
        if ln.startswith(key + "="):
            lines[i] = f"{key}={value}"
            break
    else:
        lines.append(f"{key}={value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", "utf-8")
    os.chmod(path, 0o600)


def load_template(j: str) -> dict:
    p = POLICIES / f"{j.upper()}.json"
    if not p.exists():
        have = sorted(x.stem for x in POLICIES.glob("*.json") if not x.name.endswith(".example.json"))
        raise SystemExit(f"no policy for jurisdiction {j!r}; available: {', '.join(have)}. Copy governance/residency/TEMPLATE.example.json to {j.upper()}.json and edit it.")
    return json.loads(p.read_text("utf-8"))


def active_policy(env: dict[str, str]) -> tuple[str, dict | None]:
    """(mode, policy data) as configured in .env, or ('off', None)."""
    mode = env.get("RESIDENCY_MODE", "off")
    if mode == "off" or not env.get("RESIDENCY_POLICY_B64"):
        return mode, None
    return mode, json.loads(base64.b64decode(env["RESIDENCY_POLICY_B64"]))


# ------------------------------------------------------------------------------------------------------------------ cloud
def default_region(cloud: str, tf_dir: pathlib.Path) -> str:
    env = os.environ.get("TF_VAR_region")
    if env:
        return env
    m = re.search(r'variable\s+"region"\s*\{[^}]*?default\s*=\s*"([^"]+)"', (tf_dir / "variables.tf").read_text("utf-8"), re.S)
    return m.group(1) if m else ""


def attestations() -> dict:
    return json.loads(ATTEST.read_text("utf-8")) if ATTEST.exists() else {}


def cloud_guard(cloud: str, region: str, env: dict[str, str] | None = None) -> tuple[bool, str]:
    """May the lifecycle wake a stage on this cloud/region? Always yes when residency is not enforced."""
    env = read_env(ENV) if env is None else env
    mode, pol = active_policy({**env, **{k: v for k, v in os.environ.items() if k.startswith("RESIDENCY_")}})
    if mode != "enforce" or not pol:
        return True, ""
    allowed = pol.get("cloud", {}).get("regions", {}).get(cloud, [])
    if region not in allowed:
        return False, (f"residency policy {pol['jurisdiction']}: {cloud} region '{region}' is not allowed (allowed: {', '.join(allowed) or 'none'}). "
                       f"Change the region (TF_VAR_region) or, as a deliberate and reviewed decision, the policy file.")
    if pol["cloud"].get("requires_attestation") and cloud not in attestations():
        return False, (f"residency policy {pol['jurisdiction']} requires evidence that the {cloud} offering is acceptable: {pol['cloud'].get('attestation_note', '')} "
                       f"Record it with:  ./securax residency attest {cloud} --ref '<certificate / audit report reference>'")
    return True, ""


# ------------------------------------------------------------------------------------------------------------------- CLI
def router_aliases() -> list[str]:
    try:
        c = json.loads((ROOT / "plugins" / "catalog.json").read_text("utf-8"))
    except OSError:
        return []
    out = [p["alias"] for p in c.get("providers", []) if p.get("kind") == "llm" and p.get("alias")]
    return out + [k for k in c.get("chains", {}) if not k.startswith("_")]


def cmd_status(a) -> int:
    env = read_env(pathlib.Path(a.env_file))
    mode, pol = active_policy(env)
    print(f"RESIDENCY_MODE={mode}   action={env.get('RESIDENCY_ACTION', 'reroute')}   jurisdiction={pol['jurisdiction'] if pol else '-'}")
    if mode == "off":
        print("  ⚠ nothing stops regulated data being sent to a model outside your jurisdiction → ./securax residency enable --jurisdiction IN")
        pol = gw().DEFAULT_POLICY
    p = gw().Policy(mode="enforce", data=pol)
    for c in pol["order"]:
        print(f"  class {c:<13} may be processed in: {', '.join(pol['classes'][c]['zones'])}")
    print("  model zones (a model with no zone is 'global'):")
    for al in router_aliases():
        z = p.model_zone(al)
        ok = [c for c in pol["order"] if p.allowed(c, z)]
        print(f"    {al:<26} {z:<7} usable for: {', '.join(ok) or 'nothing sensitive'}")
    if pol.get("cloud"):
        att = attestations()
        for cl, regs in pol["cloud"].get("regions", {}).items():
            print(f"  cloud {cl:<6} regions: {', '.join(regs)}   attested: {'yes (' + att[cl]['ref'] + ')' if cl in att else 'NO'}")
    return 0


def cmd_enable(a) -> int:
    env_path = pathlib.Path(a.env_file)
    pol = load_template(a.jurisdiction)
    bad = gw().problems(pol)
    if bad:
        raise SystemExit("policy is invalid: " + "; ".join(bad))
    set_env(env_path, "RESIDENCY_MODE", "monitor" if a.monitor else "enforce")
    set_env(env_path, "RESIDENCY_ACTION", a.action)
    set_env(env_path, "RESIDENCY_POLICY_B64", base64.b64encode(json.dumps(pol, separators=(",", ":")).encode()).decode())
    print(f"✔ residency {'MONITOR (logs violations, changes nothing)' if a.monitor else 'ENFORCED'} for {pol['jurisdiction']}, action={a.action}. Restart to apply:  ./securax down && ./securax up")
    print("  Check what it means for your router:  ./securax residency status")
    return 0


def cmd_disable(a) -> int:
    set_env(pathlib.Path(a.env_file), "RESIDENCY_MODE", "off")
    print("residency off. Restart to apply:  ./securax down && ./securax up")
    return 0


def cmd_check(a) -> int:
    env = read_env(pathlib.Path(a.env_file))
    mode, pol = active_policy(env)
    p = gw().Policy(mode="enforce", action=env.get("RESIDENCY_ACTION", "reroute"), data=pol or gw().DEFAULT_POLICY)
    f = type("F", (), {"rule": "PII-" + a.finding})() if a.finding else None
    d = p.decide(a.model, [f] if f else [], ident_class=a.cls)
    print(f"class={d.cls} → {d.action.upper()}: {d.reason}" + (f"  (model used: {d.model})" if d.action == "rerouted" else ""))
    return 0 if d.action in ("allow", "rerouted") else 1


def cmd_region(a) -> int:
    ok, msg = cloud_guard(a.cloud, a.region, {**read_env(pathlib.Path(a.env_file))})
    print("allowed" if ok else "REFUSED: " + msg)
    return 0 if ok else 1


def cmd_attest(a) -> int:
    att = attestations()
    att[a.cloud] = {"ref": a.ref, "by": a.by or os.environ.get("USER", "unknown"), "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    ATTEST.parent.mkdir(parents=True, exist_ok=True)
    ATTEST.write_text(json.dumps(att, indent=1), "utf-8")
    print(f"recorded for {a.cloud}: {a.ref} (by {att[a.cloud]['by']}). This is YOUR assertion; SecuRAX does not verify it.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--env-file", default=str(ENV))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    en = sub.add_parser("enable")
    en.add_argument("--jurisdiction", required=True)
    en.add_argument("--action", choices=["reroute", "block"], default="reroute")
    en.add_argument("--monitor", action="store_true")
    sub.add_parser("disable")
    ck = sub.add_parser("check")
    ck.add_argument("--class", dest="cls", default="", help="the caller's default class")
    ck.add_argument("--finding", default="", help="a detected PII label, e.g. AADHAAR")
    ck.add_argument("--model", default="bank-assistant")
    rg = sub.add_parser("region")
    rg.add_argument("cloud")
    rg.add_argument("region")
    at = sub.add_parser("attest")
    at.add_argument("cloud")
    at.add_argument("--ref", required=True)
    at.add_argument("--by", default="")
    a = ap.parse_args(argv)
    return {"status": cmd_status, "enable": cmd_enable, "disable": cmd_disable, "check": cmd_check, "region": cmd_region, "attest": cmd_attest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
