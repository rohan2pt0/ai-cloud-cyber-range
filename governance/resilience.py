#!/usr/bin/env python3
"""Can the estate carry on with any machine off? Every combination, checked by the estate itself (doc 91).

    ./securax resilience              every combination of your machines being on or off: what keeps working, what slows
                                      down, what stops, each single point of failure, and the fix for each, worst first
    ./securax resilience --json       the same, for the cockpit and routines
    ./securax resilience publish      this node's capability card, shared with every other node through sync (routine node-card)
    ./securax resilience card         print this node's card (what it can do; no secret is in it)
    ./securax resilience --notify-new send a message when a NEW single point of failure appears (routine resilience-check)

How it knows. Each node writes a small card of what it can do (a cloud key? the tunnel? the password manager? fresh backups?)
into the shared sync data, so every node knows every other node, even one that is off now (its last card is kept).
governance/resilience.json says, for every feature, what a node needs for it to work at all and at its best. With n
machines there are 2^n - 1 ways for some of them to be on; each is checked. A feature that stops, or slows down, when ONE
machine is off is a single point of failure, and is named with its fix. Nobody has to think of the scenario first.

Early warning. Each card publish also records whether each peer answered. A peer that misses far more sync rounds today
than it usually does is flagged before it fails outright.

One node at a time. Routines that message a person (`"once": true` in routines/jobs.json) run only on the first node, by name,
whose card is fresh, so three machines do not send three copies. If that node stops, the next one takes over within 25
minutes. When in doubt, a node runs the routine: a duplicate is better than nothing. Standard library only.
Exit codes: 0 no critical single point of failure, 1 one or more, 2 bad usage.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = ROOT / "governance" / "resilience.json"
ENVF = ROOT / "local" / "compose" / ".env"
HUB = os.environ.get("SECURAX_SYNC_URL", "http://127.0.0.1:8088/sync")
ESTATE_USER = "_estate"                       # the shared sync record that holds the nodes' cards
FRESH_S = 25 * 60                             # a card newer than this means the node is up now
KEEP_CARD_DAYS = 30                           # an older card is a node that is gone
MAX_NODES = 10                                # 2^10 - 1 = 1023 scenarios: plenty for one person's estate
HEALTH_KEEP = 5000                            # samples kept (bounded, doc 80)
KEY_NAMES = ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MISTRAL_API_KEY",
             "DEEPSEEK_API_KEY", "XAI_API_KEY", "PERPLEXITY_API_KEY", "OPENCODE_GO_API_KEY", "OPENROUTER_PRO_API_KEY")


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SECURAX_HOME_DIR") or pathlib.Path.home() / ".securax")


def env(key: str, default: str = "") -> str:
    if os.environ.get(key):
        return os.environ[key]
    try:
        for line in ENVF.read_text("utf-8").splitlines():
            if line.startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return default


def model(path: pathlib.Path = MODEL) -> dict:
    return json.loads(path.read_text("utf-8"))


def node_name() -> str:
    return env("SYNC_NODE_NAME") or socket.gethostname().split(".")[0] or "this-machine"


# ------------------------------------------------------------------------------------------------------- this node's card
def card(now: float | None = None) -> dict:
    """What this node can do. Counts and yes/no only: never a key, a path or a name from your data."""
    now = now or time.time()
    checks = ["estate"]
    if any(env(k) for k in KEY_NAMES) or env("REMOTE_OLLAMA_BASE"):
        checks.append("strong_ai")
    if env("CF_TUNNEL_TOKEN"):
        checks.append("online")
    if "passwords" in env("SECURAX_OPTIONAL").split():
        checks.append("passwords")
    vault = ROOT / "vault"
    if vault.is_dir() and any(p.is_file() and not p.name.startswith(".") for p in vault.rglob("*")):
        checks.append("vault")
    bdir = pathlib.Path(env("SECURAX_BACKUP_DIR") or ROOT / "backups").expanduser()
    fresh = [f for f in bdir.glob("securax-*.tar.gz*") if "-SUSPECT" not in f.name and now - f.stat().st_mtime < 2 * 86400] if bdir.is_dir() else []
    if fresh:
        checks.append("backups")
    if env("SECURAX_OFFSITE_DIR") and env("SECURAX_BACKUP_KEYFILE"):
        checks.append("offsite")
    try:
        cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        cron = ""
    if "routines run" in cron:
        checks.append("routines")
    return {"name": node_name(), "at": int(now), "checks": checks}


def _req(method: str, url: str, body: dict | None = None, timeout: float = 5) -> tuple[int, dict | None]:
    tok = next((t.strip() for t in env("SYNC_TOKENS").split(",") if t.strip()), "")
    data = json.dumps(body).encode() if body is not None else None
    hdr = {"Authorization": f"Bearer {tok}", **({"Content-Type": "application/json"} if data else {})}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=hdr, method=method), timeout=timeout) as r:  # noqa: S310
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (OSError, ValueError):
        return 0, None


def cards(fetch=_req, now: float | None = None) -> list[dict]:
    """Every node's last card (from the shared sync data), plus this node's own card, freshest first. Gone nodes drop out."""
    now = now or time.time()
    st, d = fetch("GET", f"{HUB}/state?user={ESTATE_USER}")
    out = {}
    for k, v in ((d or {}).get("payload") or {}).items() if st == 200 else []:
        if k.startswith("node:") and isinstance(v, dict) and now - float(v.get("at", 0)) < KEEP_CARD_DAYS * 86400:
            out[v.get("name") or k[5:]] = v
    me = card(now)
    out[me["name"]] = me
    return sorted(out.values(), key=lambda c: -c.get("at", 0))[:MAX_NODES]


def publish(fetch=_req, say=print, now: float | None = None) -> int:
    now = now or time.time()
    me = card(now)
    st, _ = fetch("PUT", f"{HUB}/state?user={ESTATE_USER}", {"payload": {f"node:{me['name']}": me},
                                                           "meta": {f"node:{me['name']}": int(now * 1000)}, "device": me["name"]})
    record_health(fetch, now)
    if st != 200:
        say(f"Could not share this node's card (sync answered {st or 'nothing'}): is the estate up?  ./securax up")
        return 1
    say(f"✔ shared this node's card: {me['name']} can do {', '.join(me['checks'])}")
    return 0


# ------------------------------------------------------------------------------------------------------- the analysis
def provides(c: dict, need: list[str]) -> bool:
    return set(need) <= set(c.get("checks", []))


def level(cap: dict, up: list[dict]) -> str:
    if any(provides(c, cap["full"]) for c in up):
        return "full"
    if any(provides(c, cap["needs"]) for c in up):
        return "slower"
    return "off"


def analyse(nodes: list[dict], m: dict | None = None, accepted: dict | None = None) -> dict:
    m = m or model()
    accepted = m.get("reference", {}).get("accepted", {}) if accepted is None else accepted
    caps = m["capabilities"]
    names = [n["name"] for n in nodes]
    scenarios = [list(s) for r in range(1, len(nodes) + 1) for s in itertools.combinations(nodes, r)]
    weak, alone = [], {}
    for cap in caps:
        best = level(cap, nodes)
        if best == "off":
            weak.append({"id": cap["id"], "critical": cap["critical"], "kind": "missing", "node": None, "now": "off", "fix": cap["fix"],
                         "when_off": cap["when_off"], "accepted": accepted.get(cap["id"])})
            continue
        for n in nodes:
            rest = [x for x in nodes if x is not n]
            without = level(cap, rest) if rest else "off"
            if (best, without) in (("full", "slower"), ("full", "off"), ("slower", "off")) and len(nodes) > 1:
                weak.append({"id": cap["id"], "critical": cap["critical"], "kind": "single point of failure", "node": n["name"],
                             "now": without, "fix": cap["fix"], "when_off": cap["when_off"], "accepted": accepted.get(cap["id"])})
    for n in nodes:
        alone[n["name"]] = {cap["id"]: level(cap, [n]) for cap in caps}
    crit = [c for c in caps if c["critical"] and c["id"] not in accepted]       # an accepted risk is a decision, not a surprise
    survive = sum(all(level(c, s) != "off" for c in crit) for s in scenarios)
    order = {"off": 0, "slower": 1}
    weak.sort(key=lambda w: (bool(w["accepted"]), not w["critical"], order.get(w["now"], 2), w["id"]))
    return {"nodes": names, "scenarios": len(scenarios), "survivable": survive, "weak": weak, "alone": alone}


def blocking(res: dict) -> list[dict]:
    return [w for w in res["weak"] if w["critical"] and not w["accepted"]]


# ------------------------------------------------------------------------------------------------------- early warning
def health_path() -> pathlib.Path:
    return home() / "resilience" / "health.jsonl"


def record_health(fetch=_req, now: float | None = None) -> None:
    st, d = fetch("GET", f"{HUB}/peers")
    if st != 200 or not isinstance(d, dict):
        return
    p = health_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = p.read_text("utf-8").splitlines() if p.exists() else []
    lines += [json.dumps({"at": int(now or time.time()), "peer": x.get("url", ""), "ok": bool(x.get("ok"))}) for x in d.get("peers", [])]
    p.write_text("\n".join(lines[-HEALTH_KEEP:]) + "\n", "utf-8")


def warnings(now: float | None = None, samples: list[dict] | None = None) -> list[str]:
    """A peer whose failure rate in the last 24 hours is far above its own usual rate (the 7 days before)."""
    now = now or time.time()
    if samples is None:
        p = health_path()
        samples = [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()] if p.exists() else []
    out = []
    for peer in sorted({s["peer"] for s in samples}):
        recent = [s for s in samples if s["peer"] == peer and now - s["at"] < 86400]
        before = [s for s in samples if s["peer"] == peer and 86400 <= now - s["at"] < 8 * 86400]
        if len(recent) < 6:
            continue
        r = sum(not s["ok"] for s in recent) / len(recent)
        b = sum(not s["ok"] for s in before) / len(before) if before else 0.0
        if r >= 0.2 and r >= 3 * b + 0.02:
            out.append(f"{peer} missed {r:.0%} of sync rounds in the last day (usually {b:.0%}): check it before it stops")
    return out


# ------------------------------------------------------------------------------------------------------- one node at a time
def leader(nodes: list[dict], me: str, now: float | None = None) -> str:
    now = now or time.time()
    alive = {n["name"] for n in nodes if now - n.get("at", 0) < FRESH_S} | {me}
    return sorted(alive)[0]


def is_leader(fetch=_req) -> bool:
    """Should THIS node run a once-per-estate routine now? Any doubt (sync down, no cards) answers yes."""
    try:
        me = node_name()
        return leader(cards(fetch), me) == me
    except Exception:  # noqa: BLE001 (fail open: a duplicate reminder is better than none)
        return True


# ------------------------------------------------------------------------------------------------------- report
def report(res: dict, say=print) -> None:
    n = len(res["nodes"])
    say(f"RESILIENCE · {n} machine(s): {', '.join(res['nodes'])}. Every combination of them being on: {res['scenarios']}.")
    say(f"In {res['survivable']} of {res['scenarios']}, every critical feature keeps working (accepted risks aside).\n")
    if n == 1:
        say("Only one machine is known, so it is a single point of failure for everything. Add a second one (a small VPS):")
        say("  ./securax nodes invite     (and on it, ./securax resilience publish)\n")
    for name, caps in res["alone"].items():
        off = [k for k, v in caps.items() if v == "off"]
        slow = [k for k, v in caps.items() if v == "slower"]
        say(f"  {name} alone: " + ("everything works" if not off and not slow else
            (f"stops: {', '.join(off)}" if off else "") + ("; " if off and slow else "") + (f"slower: {', '.join(slow)}" if slow else "")))
    shown = [w for w in res["weak"] if w["critical"]] + [w for w in res["weak"] if not w["critical"]][:5]
    if shown:
        say("\nSingle points of failure, worst first:")
    for w in shown:
        where = f"only {w['node']} provides it fully" if w["node"] else "no machine provides it"
        tag = "accepted" if w["accepted"] else ("CRITICAL" if w["critical"] else "minor")
        say(f"  {'·' if w['accepted'] else '✗'} [{tag}] {w['id']}: {where}; without it, {w['now']}. {w['when_off']}")
        say(f"      fix: {w['fix']}" + (f"   (accepted: {w['accepted']})" if w["accepted"] else ""))
    for line in warnings():
        say("  ⚠ " + line)
    if not blocking(res):
        say("\nNo critical single point of failure that is not accepted.")


def notify_new(res: dict) -> int:
    seen_p = home() / "resilience" / "seen.json"
    try:
        seen = set(json.loads(seen_p.read_text("utf-8")))
    except (OSError, ValueError):
        seen = set()
    now = {f"{w['id']}@{w['node']}" for w in blocking(res)}
    new = sorted(now - seen) + [f"warning: {w}" for w in warnings()]
    seen_p.parent.mkdir(parents=True, exist_ok=True)
    seen_p.write_text(json.dumps(sorted(now)), "utf-8")
    if new:
        msg = "New weak point in your estate: " + "; ".join(new[:5]) + ". See: ./securax resilience"
        subprocess.run([sys.executable, str(ROOT / "governance" / "notify.py"), "send", msg, "--title", "SecuRAX resilience"],
                       capture_output=True, timeout=60)
        print(msg)
    return 1 if now else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="resilience", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", nargs="?", default="report", choices=["report", "publish", "card"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--notify-new", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "card":
        print(json.dumps(card(), indent=1))
        return 0
    if a.cmd == "publish":
        return publish()
    res = analyse(cards())
    if a.notify_new:
        return notify_new(res)
    if a.json:
        print(json.dumps({**res, "warnings": warnings()}, indent=1))
    else:
        report(res)
    return 1 if blocking(res) else 0


if __name__ == "__main__":
    sys.exit(main())
