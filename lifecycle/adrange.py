#!/usr/bin/env python3
"""The RANGE — a dormant Active Directory practice lab (GOAD), with SecuRAX's lifecycle verbs.

Nature's pattern: a seed bank. The recipe (a pinned commit) costs nothing to keep; the lab only exists while you are practising;
sleeping it keeps its disks; the snapshot is the way back to a known-good state after you wreck a domain on purpose.

What this module is NOT: it does not re-implement an AD lab. GOAD does that, well. We add: a host check that says which lab FITS
(with real RAM numbers), a pinned and verified fetch, safety rails (isolation, cloud-cost consent, typed prune) and one set of verbs.

Standard library only. `soil` and `plan` run nowhere near a hypervisor; `install/wake/...` call GOAD, which needs its own tools.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME_DIR = os.environ.get("SECURAX_HOME_DIR") or os.path.join(os.path.expanduser("~"), ".securax")
RANGE_DIR = os.path.join(HOME_DIR, "range")
GOAD_DIR = os.path.join(RANGE_DIR, "GOAD")


def cfg() -> dict:
    with open(os.path.join(HERE, "range.json"), encoding="utf-8") as f:
        return json.load(f)


def say(msg: str = "") -> None:
    print(msg, flush=True)


def sh(argv: list[str], cwd: str | None = None, timeout: int | None = None, capture: bool = True) -> tuple[int, str]:
    try:
        p = subprocess.run(argv, cwd=cwd, text=True, timeout=timeout,
                           stdout=subprocess.PIPE if capture else None, stderr=subprocess.STDOUT if capture else None)
    except FileNotFoundError:
        return 127, f"{argv[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    return p.returncode, (p.stdout or "") if capture else ""


# ───────────────────────────────────────────── what fits on this machine ─────────────────────────────────────────────
def host() -> dict:
    """RAM / CPUs / free disk / hypervisors. SECURAX_SIM_MEM_MB lets tests (and a curious you) ask 'what if I had 32 GB?'"""
    mem = os.environ.get("SECURAX_SIM_MEM_MB")
    if mem:
        ram = int(mem)
    else:
        ram = 0
        try:
            for line in open("/proc/meminfo", encoding="utf-8"):
                if line.startswith("MemTotal:"):
                    ram = int(line.split()[1]) // 1024
                    break
        except OSError:
            pass
    try:
        wsl = "microsoft" in open("/proc/version", encoding="utf-8").read().lower()
    except OSError:
        wsl = False
    os.makedirs(HOME_DIR, exist_ok=True)
    return {"ram_mb": ram, "cpus": os.cpu_count() or 1, "free_gb": shutil.disk_usage(HOME_DIR).free // (1 << 30), "wsl": wsl,
            "kvm": os.path.exists("/dev/kvm"),
            "tools": {t: shutil.which(t) is not None for t in ("vboxmanage", "vagrant", "virsh", "terraform", "ansible", "git", "python3")}}


def fitting_labs(h: dict, c: dict | None = None) -> list[str]:
    """Labs whose RAM fits with the seed's reserve to spare, biggest first."""
    c = c or cfg()
    room = h["ram_mb"] - c["reserve_ram_mb"]
    ok = [(v["ram_mb"], k) for k, v in c["labs"].items() if v["ram_mb"] <= room]
    return [k for _, k in sorted(ok, reverse=True)]


def soil_report(h: dict | None = None) -> tuple[list[str], str | None]:
    """(lines to print, recommended lab or None)."""
    c, h = cfg(), h or host()
    out = [f"this machine: {h['ram_mb'] // 1024} GB RAM, {h['cpus']} CPUs, {h['free_gb']} GB free disk"
           + (" · WSL (cannot run VirtualBox/VMware inside it)" if h["wsl"] else "")
           + (" · KVM present" if h["kvm"] else "")]
    fits = fitting_labs(h, c)
    rec = fits[0] if fits else None
    for name, lab in sorted(c["labs"].items(), key=lambda kv: kv[1]["ram_mb"]):
        mark = "✔ fits" if name in fits else "✘ too big"
        out.append(f"  {mark:<10} {name:<11} {lab['vms']} VMs · {lab['ram_mb'] // 1000} GB RAM · {lab['vcpu']} vCPU   {lab['what']}")
    out.append(f"  (each lab needs its RAM PLUS ~{c['reserve_ram_mb'] // 1024} GB left for your OS and the SecuRAX seed)")
    if rec:
        out.append(f"recommended here: {rec}")
    else:
        need = min(v["ram_mb"] for v in c["labs"].values()) + c["reserve_ram_mb"]
        out.append(f"no lab fits this machine ({need // 1024} GB RAM is the minimum for MINILAB). Use a dedicated box (the burrow), or a cloud provider for a few hours.")
    return out, rec


def provider_advice(h: dict) -> str:
    local = h["tools"]["vboxmanage"] and h["tools"]["vagrant"] and not h["wsl"]
    if local:
        return "virtualbox (VirtualBox + Vagrant found)"
    if h["wsl"]:
        return "not from inside WSL: run GOAD on the Windows host with VirtualBox, or on a dedicated Proxmox/Ludus box, or a cloud provider"
    return "install VirtualBox + Vagrant, or use a dedicated Proxmox/Ludus box (your burrow), or a cloud provider"


# ───────────────────────────────────────────── pinned fetch ─────────────────────────────────────────────
def fetch() -> str:
    """Fetch GOAD at the pinned commit and VERIFY it. Idempotent. Raises SystemExit with the fix on failure."""
    c = cfg()
    pin = c["ref"]
    if os.path.isdir(os.path.join(GOAD_DIR, ".git")):
        rc, head = sh(["git", "rev-parse", "HEAD"], cwd=GOAD_DIR, timeout=30)
        if rc == 0 and head.strip() == pin:
            return GOAD_DIR
    os.makedirs(GOAD_DIR, exist_ok=True)
    for step in (["git", "init", "-q"], ["git", "remote", "remove", "origin"], ["git", "remote", "add", "origin", c["repo"]],
                 ["git", "fetch", "-q", "--depth", "1", "origin", pin], ["git", "checkout", "-q", "--force", "FETCH_HEAD"]):
        rc, out = sh(step, cwd=GOAD_DIR, timeout=600)
        if rc != 0 and step[1] != "remote":
            raise SystemExit(f"range: '{' '.join(step)}' failed:\n{out[-600:]}\nCheck your connection (and any proxy CA), then retry.")
    rc, head = sh(["git", "rev-parse", "HEAD"], cwd=GOAD_DIR, timeout=30)
    if head.strip() != pin:
        raise SystemExit(f"range: fetched {head.strip()[:12]} but the pin is {pin[:12]}: refusing to use it.")
    return GOAD_DIR


# ───────────────────────────────────────────── plan / run ─────────────────────────────────────────────
def check_args(lab: str, provider: str) -> dict:
    c = cfg()
    if lab not in c["labs"]:
        raise SystemExit(f"unknown lab '{lab}'. Labs: {', '.join(c['labs'])}")
    if provider not in c["providers"]:
        raise SystemExit(f"unknown provider '{provider}'. Providers: {', '.join(c['providers'])}")
    return c


def goad_argv(task: str, lab: str, provider: str) -> list[str]:
    c = check_args(lab, provider)
    return ["bash", "goad.sh", "-t", c["tasks"][task], "-l", lab, "-p", provider]


def plan(lab: str, provider: str) -> list[str]:
    c = check_args(lab, provider)
    p = c["providers"][provider]
    lines = [f"lab {lab} on {provider} — {p['note']}", "", "commands (run inside the pinned GOAD checkout, ~/.securax/range/GOAD):"]
    for t in ("install", "wake", "hibernate", "snapshot", "reset", "prune"):
        lines.append("  " + " ".join(goad_argv(t, lab, provider)[1:]) + f"      # {t}")
    lines += ["", "read before you start:"] + [f"  ! {w}" for w in c["warnings"]]
    if p["kind"] == "cloud":
        lines.append("  ! cloud: a VULNERABLE lab in your account. Isolate it (no public IPs), set a billing alarm, and destroy it when done.")
    return lines


def run_task(task: str, lab: str, provider: str, consent_cloud: bool = False) -> int:
    c = check_args(lab, provider)
    if c["providers"][provider]["kind"] == "cloud" and not consent_cloud:
        say(f"! {provider} is a CLOUD provider: it bills real money and hosts a deliberately vulnerable network.\n  Re-run with --i-accept-cloud-cost once you have a billing alarm and have read: ./securax range plan --lab {lab} --provider {provider}")
        return 2
    if task != "install" and not os.path.isdir(os.path.join(GOAD_DIR, ".git")):
        say("The range has not been installed yet (it is dormant). Start with:  ./securax range install --lab MINILAB --provider virtualbox")
        return 1
    d = fetch()
    argv = goad_argv(task, lab, provider)
    say(f"→ {' '.join(argv[1:])}   (in {d})")
    return sh(argv, cwd=d, capture=False)[0]


def prune(lab: str, provider: str, typed: str, consent_cloud: bool = False) -> int:
    """Destroy the lab's VMs (GOAD 'destroy'), then forget the checkout. Needs the typed phrase."""
    if typed != f"PRUNE range {lab}":
        say(f"cancelled — nothing was changed. (To confirm, type exactly: PRUNE range {lab})")
        return 1
    rc = run_task("prune", lab, provider, consent_cloud) if os.path.isdir(os.path.join(GOAD_DIR, ".git")) else 0
    if rc == 0:
        shutil.rmtree(RANGE_DIR, ignore_errors=True)
        say("The range was destroyed and the checkout removed. The recipe is still in range.json: install it again any time.")
    return rc


def status() -> str:
    """dormant (never fetched) | fetched (recipe present, lab not asked about). The live VM state is GOAD's: `range status`."""
    return "fetched" if os.path.isdir(os.path.join(GOAD_DIR, ".git")) else "dormant"


if __name__ == "__main__":
    sys.exit("run via ./securax range …")
