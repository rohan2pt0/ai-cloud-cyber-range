"""The lite range: the Linux side of a scenario as small containers on the laptop, isolated from every real network.

Every zone is a Docker network with `internal: true`, so nothing in the range can reach the internet or your LAN, and
nothing outside can reach it, apart from one door: the blue team's jump box on 127.0.0.1:2222. Inside:

    hosts marked "gamebox"   run the services their scored checks name (ssh, web, dns, smtp) with the scenario's staff accounts
    the jump box             the blue team's way in (SSH as the scenario's admin), with a leg in every zone at .250
    the scoring bot          checks every service from inside each zone (.252) and logs in as the simulated staff
    the red-team bot         sits in the zones an outsider reaches (.251) and tries the original passwords in the attack phase

Windows machines (domain controllers, Exchange, SQL Server, desktops) are not containers: hosts marked "goad" come from the
GOAD lab (`./securax range`), "skip" ones exist only in the full cloud range. Both show as "not deployed" here.
"""
from __future__ import annotations

import hashlib
import html
import ipaddress
import json
import pathlib
import shutil
import subprocess

from . import scenario as scn

HERE = pathlib.Path(__file__).resolve().parent
BOX = HERE / "gamebox"
SERVICE_OF = {"ssh": "ssh", "http": "http", "dns": "dns", "smtp": "smtp"}
RED_ZONES = ("dmz", "cloud", "wifi")            # where an outsider lands in the sample; a scenario may set "red_zones"
RAM_MB = {"host": 24, "jump": 24, "tool": 64}


def image_tag() -> str:
    h = hashlib.sha256(b"".join((BOX / f).read_bytes() for f in ("Dockerfile", "entrypoint.sh", "svc"))).hexdigest()[:12]
    return f"securax-exercise-gamebox:{h}"


def deployed(sc: dict) -> list[dict]:
    return [h for h in sc["hosts"] if h.get("lite") in ("gamebox", "jump")]


def scored_rows(sc: dict) -> list[dict]:
    names = {h["name"] for h in deployed(sc)}
    return [r for r in scn.checks(sc) if r["host"] in names]


def plan(sc: dict) -> dict:
    hosts = deployed(sc)
    goad = [h["name"] for h in sc["hosts"] if h.get("lite") == "goad"]
    skip = [h["name"] for h in sc["hosts"] if h.get("lite") == "skip"]
    ram = sum(RAM_MB["jump" if h.get("lite") == "jump" else "host"] for h in hosts) + 2 * RAM_MB["tool"]
    return {"containers": len(hosts) + 2, "hosts": [h["name"] for h in hosts], "goad": goad, "full_range_only": skip, "ram_mb": ram,
            "checks_scored_here": len(scored_rows(sc)), "checks_in_scenario": len(scn.checks(sc))}


def clashes(sc: dict, routes: str | None = None) -> list[str]:
    """Zone subnets that overlap a network this machine already routes to (a VPN, the office LAN): refuse rather than break it."""
    if routes is None:
        try:
            routes = subprocess.run(["ip", "-4", "route"], capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            return []
    have = []
    for ln in routes.splitlines():
        f = ln.split()
        dev = f[f.index("dev") + 1] if "dev" in f[:-1] else ""
        if not f or f[0] == "default" or dev.startswith(("docker", "br-", "veth")):     # Docker's own bridges, ours included
            continue
        try:
            have.append((ipaddress.ip_network(f[0], strict=False), dev))
        except ValueError:
            pass
    return [f"zone {z} ({d['cidr']}) overlaps {n} on {dev or 'this machine'}" for z, d in sc["zones"].items()
            for n, dev in have if ipaddress.ip_network(d["cidr"]).overlaps(n)]


def write(sc: dict, game_dir: pathlib.Path, repo: pathlib.Path) -> pathlib.Path:
    """Write lite/compose.json and every host's read-only config folder. Returns the compose file."""
    out = game_dir / "lite"
    if (out / "hosts").exists():
        shutil.rmtree(out / "hosts")
    (out / "hosts").mkdir(parents=True)
    admin = sc["admin"]
    dns_hosts = "\n".join(f"{h['ip']} {h['name']}.{sc['domain']} {h['name']}" for h in sc["hosts"]) + "\n"
    zones_used = sorted({h["zone"] for h in deployed(sc)} | set(sc.get("red_zones", RED_ZONES)) & set(sc["zones"]))
    nets = {f"z-{z}": {"internal": True, "ipam": {"config": [{"subnet": sc["zones"][z]["cidr"]}]}} for z in zones_used}
    nets["access"] = {"internal": False}
    tag = image_tag()
    services = {}
    for h in deployed(sc):
        cfg = out / "hosts" / h["name"]
        cfg.mkdir()
        users = [(admin["username"], admin["password"])] + [(u["username"], u["password"]) for u in sc["users"] if h["name"] in u.get("hosts", [])]
        (cfg / "users").write_text("".join(f"{n}:{p}\n" for n, p in users))
        org, about = html.escape(sc["org"]), html.escape(h.get("about", ""))
        (cfg / "index.html").write_text(f"<!doctype html><title>{org}</title><h1>{org}</h1><p>{about}</p>\n")
        (cfg / "dns-hosts").write_text(dns_hosts)
        (cfg / "domain").write_text(sc["domain"] + "\n")
        pub = out / "greenteam_ed25519.pub"
        if sc.get("green_team") and pub.exists():
            (cfg / "green_user").write_text(sc["green_team"]["username"] + "\n")
            (cfg / "green_key.pub").write_text(pub.read_text())
        svcs = sorted({SERVICE_OF[s["check"]] for s in h.get("services", []) if s["check"] in SERVICE_OF} | ({"ssh"} if h.get("lite") == "jump" else set()))
        networks = {f"z-{h['zone']}": {"ipv4_address": h["ip"]}}
        if h.get("lite") == "jump":
            networks.update({f"z-{z}": {"ipv4_address": scn.reserved(sc, z, 250)} for z in zones_used if z != h["zone"]})
            networks["access"] = {}
        svc = {"image": tag, "hostname": h["name"], "container_name": f"{_proj(game_dir)}-{h['name']}", "networks": networks,
               "environment": {"ROLE": "host", "SERVICES": ",".join(svcs), "ADMIN": admin["username"]},
               "volumes": [f"./hosts/{h['name']}:/range-config:ro"], "restart": "unless-stopped", "mem_limit": "128m", "pids_limit": 256}
        if h.get("lite") == "jump":
            svc["ports"] = ["127.0.0.1:2222:22"]
        services[h["name"]] = svc
    tool = {"image": tag, "environment": {"ROLE": "tool", "PYTHONDONTWRITEBYTECODE": "1"}, "working_dir": "/securax",
            "volumes": [f"{repo / 'exercise'}:/securax/exercise:ro", f"{game_dir}:/game"],     # only the exercise code: never the rest of the vault
            "restart": "on-failure", "mem_limit": "256m", "pids_limit": 256}
    services["scoring-bot"] = {**tool, "container_name": f"{_proj(game_dir)}-scoring-bot",
                               "command": ["python3", "-m", "exercise", "run", "--game", "/game", "--lite"],
                               "networks": {f"z-{z}": {"ipv4_address": scn.reserved(sc, z, 252)} for z in zones_used}}
    services["red-bot"] = {**tool, "container_name": f"{_proj(game_dir)}-red-bot", "command": ["python3", "-m", "exercise", "redbot", "--game", "/game"],
                           "networks": {f"z-{z}": {"ipv4_address": scn.reserved(sc, z, 251)} for z in sorted(set(sc.get("red_zones", RED_ZONES)) & set(zones_used))}}
    compose = {"name": _proj(game_dir), "services": services, "networks": nets}
    f = out / "compose.json"
    f.write_text(json.dumps(compose, indent=1))
    return f


def _proj(game_dir: pathlib.Path) -> str:
    return "sxex-" + "".join(c if c.isalnum() else "-" for c in game_dir.name.lower())[:40]


def compose(game_dir: pathlib.Path, *args: str, timeout: int = 900) -> tuple[int, str]:
    f = game_dir / "lite" / "compose.json"
    p = subprocess.run(["docker", "compose", "-f", str(f), "-p", _proj(game_dir), *args], capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)[-3000:]


def green_key(game_dir: pathlib.Path) -> pathlib.Path:
    """This exercise's green-team key pair (made once, with the range image's ssh-keygen, so the host needs no SSH tools)."""
    out = game_dir / "lite"
    out.mkdir(parents=True, exist_ok=True)
    key = out / "greenteam_ed25519"
    if not key.exists():
        subprocess.run(["docker", "run", "--rm", "-e", "ROLE=tool", "-v", f"{out}:/k", image_tag(), "ssh-keygen", "-q", "-t", "ed25519", "-N", "",
                        "-C", "exercise-green-team", "-f", "/k/greenteam_ed25519"], capture_output=True, timeout=120, check=True)
    return key


def build(timeout: int = 900) -> tuple[int, str]:
    tag = image_tag()
    if subprocess.run(["docker", "image", "inspect", tag], capture_output=True).returncode == 0:
        return 0, f"{tag} already built"
    p = subprocess.run(["docker", "build", "-q", "-t", tag, str(BOX)], capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)[-3000:]
