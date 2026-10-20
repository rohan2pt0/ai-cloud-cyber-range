"""Scenario files: one JSON file describes a whole exercise for any team number.

A scenario names the zones, the hosts in each zone, the services the scoring bots must find working, the simulated staff and
their passwords, the tasks on the mission board, the news injects and the scoring rules. Addresses are templates: `{X}` is the
team number, and simple arithmetic is allowed (`10.188.33.{X*4-2}`), so one file serves team 1 and team 72 alike.

`load(path, team)` returns the scenario with every template filled in, or raises ValueError listing every problem at once.
Real exercise scenarios hold private detail and belong in vault/exercise/scenarios/; the repository ships only a fictional sample.
"""
from __future__ import annotations

import ast
import copy
import ipaddress
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
SAMPLE = HERE / "scenarios" / "sample.json"
CHECKS = ("tcp", "ssh", "http", "https", "dns", "smtp", "ping")
LITE = ("gamebox", "jump", "goad", "skip")
SCORING_DEFAULTS = {"round_seconds": 60, "availability_per_check": 1, "rule_breach_per_round": -5, "usersim_per_login": 1, "attack_report": -40,
                    "restore_from_backup": -25, "hint_fraction": 0.2, "abandon_fraction": 0.5, "incident_report_max": 20,
                    "situation_report_per_grade": 4, "situation_report_max_grade": 5, "compromised_minutes": 60}
_TEMPLATE = re.compile(r"\{([^{}]*)\}")
_ALLOWED = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.USub, ast.Constant, ast.Name, ast.Load)


def _calc(expr: str, team: int) -> int:
    """Arithmetic on the team number only: + - * // and parentheses. Anything else is refused, never run."""
    tree = ast.parse(expr.strip(), mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED) or (isinstance(node, ast.Name) and node.id != "X") or (isinstance(node, ast.Constant) and not isinstance(node.value, int)):
            raise ValueError(f"template {{{expr}}}: only the team number X, whole numbers and + - * // are allowed")
    return int(eval(compile(tree, "<template>", "eval"), {"__builtins__": {}}, {"X": team}))  # noqa: S307 (checked above)


def fill(value, team: int):
    if isinstance(value, str):
        return _TEMPLATE.sub(lambda m: str(_calc(m.group(1), team)), value)
    if isinstance(value, list):
        return [fill(v, team) for v in value]
    if isinstance(value, dict):
        return {k: fill(v, team) for k, v in value.items()}
    return value


def problems(sc: dict) -> list[str]:
    out = []
    for key in ("name", "zones", "hosts", "admin"):
        if key not in sc:
            out.append(f"missing '{key}'")
    if out:
        return out
    nets = {}
    for z, d in sc["zones"].items():
        try:
            nets[z] = ipaddress.ip_network(d["cidr"])
        except (KeyError, ValueError) as e:
            out.append(f"zone {z}: bad cidr ({e})")
    names, ips = set(), set()
    for h in sc["hosts"]:
        n = h.get("name", "?")
        if n in names:
            out.append(f"host {n}: listed twice")
        names.add(n)
        if h.get("zone") not in sc["zones"]:
            out.append(f"host {n}: unknown zone {h.get('zone')!r}")
        try:
            ip = ipaddress.ip_address(h.get("ip", ""))
            if h.get("zone") in nets and ip not in nets[h["zone"]]:
                out.append(f"host {n}: {ip} is outside zone {h['zone']} ({nets[h['zone']]})")
            if ip in ips:
                out.append(f"host {n}: address {ip} is used twice")
            ips.add(ip)
            if h.get("zone") in nets and int(ip) - int(nets[h["zone"]].network_address) >= 250:
                out.append(f"host {n}: addresses .250 and above are kept for the scoring bot, user simulation and red team")
        except ValueError:
            out.append(f"host {n}: bad address {h.get('ip')!r}")
        if h.get("lite", "skip") not in LITE:
            out.append(f"host {n}: lite must be one of {', '.join(LITE)}")
        for s in h.get("services", []):
            if s.get("check") not in CHECKS:
                out.append(f"host {n} service {s.get('name')}: check must be one of {', '.join(CHECKS)}")
            if s.get("check") != "ping" and (not isinstance(s.get("port"), int) or not 0 < s["port"] < 65536):
                out.append(f"host {n} service {s.get('name')}: bad port")
    for u in sc.get("users", []):
        for hn in u.get("hosts", []):
            if hn not in names:
                out.append(f"user {u.get('username')}: unknown host {hn}")
    gt = sc.get("green_team")
    if gt and not str(gt.get("username", "")).isidentifier():
        out.append("green_team.username must be a plain account name")
    pids = [i.get("id") for i in sc.get("playbook", [])]
    if len(pids) != len(set(pids)) or any(not isinstance(i.get("from_minute"), int) or not isinstance(i.get("to_minute"), int)
                                          or i["to_minute"] < i["from_minute"] for i in sc.get("playbook", [])):
        out.append("playbook items need unique ids and whole-number from_minute <= to_minute")
    from . import frameworks as fw
    cat = fw.load()
    for t in sc.get("tasks", []):
        for bad in fw.unknown(fw.tags(t), cat):
            out.append(f"task {t.get('id')}: {bad} is not a known ATT&CK, D3FEND or ATLAS identifier in exercise/frameworks.json")
    ids = [t.get("id") for t in sc.get("tasks", [])]
    if len(ids) != len(set(ids)):
        out.append("task ids must be unique")
    for t in sc.get("tasks", []):
        if not isinstance(t.get("points"), int) or t["points"] <= 0:
            out.append(f"task {t.get('id')}: points must be a positive whole number")
    return out


def load(path: pathlib.Path | str | None = None, team: int | None = None) -> dict:
    raw = json.loads(pathlib.Path(path or SAMPLE).read_text("utf-8"))
    t = int(team if team is not None else raw.get("team_default", 1))
    if not 1 <= t <= 250:
        raise ValueError("team number must be 1 to 250")
    try:
        sc = fill(copy.deepcopy(raw), t)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"{pathlib.Path(path or SAMPLE).name}: {e}") from None
    sc["team"] = t
    sc["scoring"] = {**SCORING_DEFAULTS, **sc.get("scoring", {})}
    sc.setdefault("users", [])
    sc.setdefault("tasks", [])
    sc.setdefault("injects", [])
    sc.setdefault("phases", [])
    sc.setdefault("rules", [])
    sc.setdefault("playbook", [])
    for h in sc.get("hosts", []):         # every machine has the exercise's "HOST" check (ping) unless the scenario says otherwise
        if h.get("ping", True) and not any(x.get("check") == "ping" for x in h.get("services", [])):
            h["services"] = [{"name": "HOST", "check": "ping", "port": 0}] + h.get("services", [])
    errs = problems(sc)
    if errs:
        raise ValueError(f"{pathlib.Path(path or SAMPLE).name} (team {t}): " + "; ".join(errs))
    return sc


def host(sc: dict, name: str) -> dict:
    for h in sc["hosts"]:
        if h["name"] == name:
            return h
    raise KeyError(name)


def checks(sc: dict) -> list[dict]:
    """Every scored check as one flat row: host, zone, service, check type, address, port and options."""
    return [{"host": h["name"], "zone": h["zone"], "service": s["name"], "check": s["check"], "ip": h["ip"], "port": s["port"],
             "expect": s.get("expect", ""), "query": s.get("query", ""), "lite": h.get("lite", "skip")}
            for h in sc["hosts"] for s in h.get("services", [])]


def reserved(sc: dict, zone: str, last: int) -> str:
    """The address .<last> in a zone: 251 red team (in the zones it can reach), 252 scoring bot, 253 user simulation."""
    net = ipaddress.ip_network(sc["zones"][zone]["cidr"])
    return str(net.network_address + last)
