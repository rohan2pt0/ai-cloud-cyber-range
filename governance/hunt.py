#!/usr/bin/env python3
"""`./securax hunt` — enterprise threat hunting & post-crisis DFIR, in minimal (offline) or fleet mode (doc 127).

After a cyber crisis the question is: where is the foothold, how far did it spread, and what did they leave to get
back in? This drives Velociraptor (the Apache-2.0 endpoint engine) to collect and hunt — as a single self-contained
OFFLINE COLLECTOR with no server (the minimal mode that fits a DevSecOps pipeline or one suspect host), or across a
fleet. It ships no proprietary binary: triage collection uses Velociraptor's open Windows.KapeFiles.Targets and native
VQL. A hunt pack names the artifacts to collect, deterministic rules that score the output into prioritised findings,
and the candidate response actions — and every action that TOUCHES an endpoint stays behind ./securax approve.

  ./securax hunt tools [--json]                  the tool manifest: each tool, its licence, whether it may be redistributed, and its status (fetch-not-vendor)
  ./securax hunt tools accept <id>               record a human's acceptance of a gated tool's EULA (audited) before it may be fetched
  ./securax hunt packs [--json]                  the hunt packs (mapped to the crisis/wargame scenarios)
  ./securax hunt plan <pack>                     what a pack collects, how it scores the output, and the actions it may warrant — no execution
  ./securax hunt collector <pack> [--out DIR]    generate a self-contained offline collector (spec + run script) for minimal/pipeline mode
  ./securax hunt auto <scenario> [--input DIR]   post-crisis automation: pick the pack for the scenario, prepare the collector, triage if results are given
  ./securax hunt triage <run> [--input DIR]      score the collected output into prioritised findings (deterministic; an AI second opinion when a gateway is up)
  ./securax hunt act <run>                        the ordered remediation plan the findings warrant — each step an approve-gated command (nothing is executed here)
  ./securax hunt report <run>                     write a post-hunt report (findings + the plan + the approve steps) to feed the crisis pack and the lessons
  ./securax hunt fleet plan|server|clients|hunt   mass-deployment (doc 129): generate the Velociraptor server setup, the client rollout (GPO/Intune/SCCM/Ansible) and a throttled fleet hunt — from your internal mirror; provisions nothing (your approved step)
  ./securax hunt sweep [--notify]                the estate watches for an open crisis with no hunt prepared and nudges — from one node only (no SPOF)
  ./securax hunt status [<run>]                  your hunt runs and their state

Runs are stored in vault/hunt-runs/ (private, never in git). Tools are fetched into vault/hunt-tools/ on use, or from
your internal mirror (SECURAX_HUNT_MIRROR) — never bundled. Tools and packs are DATA (governance/hunt-tools.json,
governance/hunt-packs.json). Standard library only; no network in this tool itself. This is a coordination and triage
aid, not a verdict and not legal advice: a human owns every endpoint action, behind ./securax approve.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TOOLS = HERE / "hunt-tools.json"
PACKS = HERE / "hunt-packs.json"
FLEET = HERE / "hunt-fleet.json"
UTC = dt.timezone.utc


def tools_lib() -> dict:
    return json.loads(TOOLS.read_text("utf-8"))


def fleet_lib() -> dict:
    return json.loads(FLEET.read_text("utf-8"))


def packs_lib() -> dict:
    return json.loads(PACKS.read_text("utf-8"))


def runs_dir() -> pathlib.Path:
    base = pathlib.Path(os.environ.get("SECURAX_HUNT_DIR") or (ROOT / "vault" / "hunt-runs"))
    base.mkdir(parents=True, exist_ok=True)
    return base


def tz() -> dt.tzinfo:
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(os.environ.get("SECURAX_TZ", "Asia/Kolkata"))
    except Exception:  # noqa: BLE001
        return dt.timezone(dt.timedelta(hours=5, minutes=30))


def iso(t: dt.datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(s: str) -> str:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(tz()).strftime("%d %b %Y %H:%M %Z")


def run_path(rid: str) -> pathlib.Path:
    return runs_dir() / f"{rid}.json"


def load_run(rid: str) -> dict:
    p = run_path(rid)
    if not p.exists():
        raise SystemExit(f"no such hunt run {rid} (see: ./securax hunt status)")
    return json.loads(p.read_text("utf-8"))


def save_run(run: dict) -> None:
    p = run_path(run["id"])
    p.write_text(json.dumps(run, indent=1) + "\n", "utf-8")
    os.chmod(p, 0o600)


def runs() -> list[dict]:
    return sorted((json.loads(p.read_text("utf-8")) for p in runs_dir().glob("HUNT-*.json")), key=lambda r: r["id"])


def _accepted_path() -> pathlib.Path:
    base = pathlib.Path(os.environ.get("SECURAX_HUNT_TOOLS_DIR") or (ROOT / "vault" / "hunt-tools"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "accepted.json"


def _accepted() -> dict:
    p = _accepted_path()
    if p.exists():
        try:
            return json.loads(p.read_text("utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def cmd_tools(a, now: dt.datetime) -> int:
    data = tools_lib()
    if a.json:
        print(json.dumps(data, indent=2))
        return 0
    accepted = _accepted()
    print(data["about"])
    mirror = os.environ.get(data.get("mirror_env", "SECURAX_HUNT_MIRROR"))
    print(f"\nFetch source: {'internal mirror ' + mirror if mirror else 'official vendor sources (set ' + data.get('mirror_env', 'SECURAX_HUNT_MIRROR') + ' for an internal mirror)'}")
    print("\nTools (fetched on use, never bundled):\n")
    for t in data["tools"]:
        redis = "redistributable" if t["redistributable"] else "NOT redistributable"
        if t["status"] == "active":
            mark = "✔ active"
        elif t["id"] in accepted:
            mark = "✔ EULA accepted"
        else:
            mark = "⛔ gated — needs: ./securax hunt tools accept " + t["id"]
        print(f"  {t['name']}")
        print(f"      {t['role']}")
        print(f"      licence: {t['licence']}  ·  {redis}  ·  {mark}")
        if t.get("licence_note"):
            print(f"      note: {t['licence_note']}")
        print(f"      source: {t['source']}")
        print()
    print("SecuRAX ships no third-party forensic binary. The non-redistributable tools above are listed for completeness;")
    print("each stays disabled until a human accepts its EULA, and is then fetched from the vendor (or your mirror), hash-pinned.")
    return 0


def cmd_tools_accept(a, now: dt.datetime) -> int:
    data = tools_lib()
    t = next((x for x in data["tools"] if x["id"] == a.id), None)
    if not t:
        print(f"no tool {a.id!r}; see ./securax hunt tools")
        return 2
    if t["status"] == "active":
        print(f"{t['name']} is {t['licence']} and needs no acceptance — it is already active.")
        return 0
    acc = _accepted()
    acc[a.id] = {"name": t["name"], "licence": t["licence"], "accepted_at": iso(now),
                 "by": os.environ.get("SECURAX_OWNER", "operator"),
                 "licence_note": t.get("licence_note", ""), "source": t["source"]}
    p = _accepted_path()
    p.write_text(json.dumps(acc, indent=1) + "\n", "utf-8")
    os.chmod(p, 0o600)
    # best-effort: record to the estate's audit trail
    try:
        subprocess.run([str(ROOT / "securax"), "notify", "send",
                        f"hunt: EULA accepted for {t['name']} ({t['licence']}) — tool may now be fetched"],
                       capture_output=True, timeout=20)
    except Exception:  # noqa: BLE001
        pass
    print(f"Recorded acceptance of the {t['name']} EULA ({t['licence']}).")
    print(f"  {t.get('licence_note', '')}")
    print("  The tool may now be fetched from its vendor source (or your internal mirror), verified against its pinned SHA-256.")
    print("  You remain responsible for holding the right to use it for your purpose.")
    return 0


def cmd_packs(a, now: dt.datetime) -> int:
    data = packs_lib()
    if a.json:
        print(json.dumps(data, indent=2))
        return 0
    print(data["about"])
    print("\nHunt packs (./securax hunt plan <id>):\n")
    for pid, p in data["packs"].items():
        print(f"  {pid:<26} {p['name']}")
        print(f"       scenario: {p['scenario']:<14} mode: {p['mode']:<8} {len(p['artifacts'])} artifacts")
        print(f"       {p['about']}")
        print()
    print(data["severity_note"])
    return 0


def _pack(pid: str) -> dict:
    data = packs_lib()
    if pid not in data["packs"]:
        raise SystemExit(f"no hunt pack {pid!r}; see ./securax hunt packs")
    return data["packs"][pid]


def cmd_plan(a, now: dt.datetime) -> int:
    p = _pack(a.pack)
    print(f"▶ Hunt pack: {p['name']}  (scenario: {p['scenario']}, mode: {p['mode']})")
    print(f"  {p['about']}\n")
    print("  Collects these Velociraptor artifacts:")
    for art in p["artifacts"]:
        print(f"    · {art}")
    print("\n  Scores the collected output by these rules (first pass to focus a human, never a verdict):")
    for r in p["triage_rules"]:
        print(f"    [{r['weight']}] {r['signal']:<22} → {r['says']}")
    print("\n  Response actions it may warrant — each a human decision behind ./securax approve:")
    for act in p["actions"]:
        print(f"    · {act['action']}  (approve: {act['approve']})  — {act['why']}")
    print(f"\n  Prepare a collector:  ./securax hunt collector {a.pack}")
    return 0


def _new_id(now: dt.datetime) -> str:
    n = 1 + sum(1 for r in runs() if r["id"].startswith(f"HUNT-{now:%Y%m%d}"))
    return f"HUNT-{now:%Y%m%d}-{n:03d}"


def _write_collector(run: dict, p: dict, out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    spec = {"name": run["id"], "pack": run["pack"], "type": "offline",
            "artifacts": p["artifacts"],
            "note": "Self-contained Velociraptor offline collection. No server required.",
            "output": f"{run['id']}-collection.zip"}
    (out / "collector-spec.json").write_text(json.dumps(spec, indent=1) + "\n", "utf-8")
    # the exact, copy-paste commands for minimal/pipeline mode — no server, one host
    lines = ["#!/usr/bin/env bash",
             "# SecuRAX hunt — offline collection (minimal mode). Run on the suspect host or in the pipeline.",
             "# Needs the velociraptor binary (fetch per governance/hunt-tools.json; never bundled). No server.",
             "set -euo pipefail",
             'VELO="${VELOCIRAPTOR:-velociraptor}"',
             f'OUT="{run["id"]}-collection.zip"',
             '"$VELO" artifacts collect \\']
    for art in p["artifacts"]:
        lines.append(f'  {art} \\')
    lines += ['  --output "$OUT"',
              'echo "collected → $OUT   then: ./securax hunt triage ' + run["id"] + ' --input <unzipped dir>"']
    sh = out / "collect.sh"
    sh.write_text("\n".join(lines) + "\n", "utf-8")
    os.chmod(sh, 0o700)
    ps = ["# SecuRAX hunt — offline collection (minimal mode), PowerShell.",
          "$Velo = if ($env:VELOCIRAPTOR) { $env:VELOCIRAPTOR } else { 'velociraptor.exe' }",
          f"$Out = '{run['id']}-collection.zip'",
          "& $Velo artifacts collect " + " ".join(p["artifacts"]) + " --output $Out"]
    (out / "collect.ps1").write_text("\n".join(ps) + "\n", "utf-8")
    readme = [f"# Hunt collector — {run['id']} ({p['name']})", "",
              "Minimal / offline mode: a self-contained Velociraptor collection, no server.", "",
              "1. Put the `velociraptor` binary on PATH (fetch per governance/hunt-tools.json; set VELOCIRAPTOR to its path).",
              "2. Run `collect.sh` (Linux/macOS target) or `collect.ps1` (Windows target) on the suspect host or in the pipeline.",
              "3. Bring the resulting zip back, unzip it, and run:",
              f"   `./securax hunt triage {run['id']} --input <unzipped dir>`", "",
              "For a fleet, run the same artifacts as a server-side hunt instead (see doc 127).", "",
              "No endpoint is changed by collection. Any response action is a human decision behind `./securax approve`."]
    (out / "README.md").write_text("\n".join(readme) + "\n", "utf-8")


def cmd_collector(a, now: dt.datetime) -> int:
    p = _pack(a.pack)
    rid = _new_id(now)
    run = {"id": rid, "pack": a.pack, "name": p["name"], "scenario": p["scenario"], "mode": "offline",
           "artifacts": p["artifacts"], "created_at": iso(now), "state": "planned", "findings": []}
    save_run(run)
    out = pathlib.Path(a.out) if a.out else (runs_dir() / rid)
    _write_collector(run, p, out)
    print(f"▶ Prepared offline collector {rid} for '{p['name']}' (no server needed):")
    for name in ("collect.sh", "collect.ps1", "collector-spec.json", "README.md"):
        print(f"    {out / name}")
    print("\n  Run it on the suspect host or in your pipeline, then bring the zip back and triage:")
    print(f"    ./securax hunt triage {rid} --input <unzipped collection dir>")
    print("  Collection changes nothing on the endpoint. Response actions stay behind ./securax approve.")
    return 0


def _scan(input_dir: pathlib.Path, rules: list[dict]) -> list[dict]:
    """Deterministic triage: scan the collected text for each rule's signal; score by weight. Offline, repeatable."""
    findings = []
    texts = []
    for fp in sorted(input_dir.rglob("*")):
        if fp.is_file() and fp.stat().st_size <= 8 * 1024 * 1024:
            try:
                texts.append((fp.name, fp.read_text("utf-8", errors="ignore").lower().replace("\\", "/")))
            except Exception:  # noqa: BLE001
                continue
    for r in rules:
        sig = r["signal"].lower().replace("\\", "/")
        hits = [name for name, body in texts if sig in body]
        if hits:
            findings.append({"id": r["id"], "signal": r["signal"], "weight": r["weight"],
                             "says": r["says"], "seen_in": sorted(set(hits))[:8]})
    findings.sort(key=lambda f: f["weight"], reverse=True)
    return findings


def _ai_triage(pack_name: str, findings: list[dict]) -> str | None:
    """Optional AI second opinion through the gateway (rails + audit). Offline-safe: None without GATEWAY_URL or on error."""
    if not os.getenv("GATEWAY_URL") or not findings:
        return None
    try:
        spec = importlib.util.spec_from_file_location("hunt_personas", ROOT / "agents" / "personas.py")
        personas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(personas)
        brief = "\n".join(f"- [{f['weight']}] {f['signal']}: {f['says']} (seen in {', '.join(f['seen_in'])})"
                          for f in findings)
        q = ("You are triaging the findings of a post-crisis endpoint hunt ('" + pack_name + "'). "
             "Given the signals below, reply in at most four short lines: the single most likely story that ties them "
             "together, the one host or artifact to look at first, and the one containment action to put to a human for "
             "approval. Do not invent signals beyond those given; do not recommend acting without human approval.\n\n"
             + brief)
        res = personas.ask_agent("negotiation", q, careful=False)
        return res.get("answer")
    except Exception:  # noqa: BLE001
        return None


def cmd_triage(a, now: dt.datetime) -> int:
    run = load_run(a.run)
    p = _pack(run["pack"])
    src = pathlib.Path(a.input) if a.input else (runs_dir() / run["id"])
    if not src.exists():
        print(f"no input at {src}. Collect first (./securax hunt collector {run['pack']}), then pass --input <dir>.")
        return 2
    findings = _scan(src, p["triage_rules"])
    run["findings"] = findings
    run["state"] = "triaged"
    run["triaged_at"] = iso(now)
    risk = sum(f["weight"] for f in findings)
    run["risk"] = risk
    save_run(run)
    out = runs_dir() / run["id"]
    out.mkdir(parents=True, exist_ok=True)
    md = [f"# Hunt triage — {run['id']} ({p['name']})", "",
          f"**Scored:** {local(iso(now))}  ·  **Scenario:** {run['scenario']}  ·  **Risk tally:** {risk}", "",
          "A first pass to focus a human, never a verdict. Every action below is a decision behind `./securax approve`.", ""]
    if findings:
        md.append("## Prioritised findings\n")
        md.append("| Priority | Signal | What it means | Seen in |")
        md.append("|---|---|---|---|")
        for f in findings:
            md.append(f"| {f['weight']} | `{f['signal']}` | {f['says']} | {', '.join(f['seen_in'])} |")
    else:
        md.append("No rule matched the collected output. That is not a clean bill of health — widen the pack, "
                  "lengthen the window, or hunt by hand.")
    ai = _ai_triage(p["name"], findings)
    if ai:
        md += ["", "## AI second opinion (through the governed gateway)", "", ai.strip(),
               "", "_A drafted hypothesis, not a verdict; a human confirms it._"]
    (out / "triage-report.md").write_text("\n".join(md) + "\n", "utf-8")
    print(f"▶ {run['id']} triaged: {len(findings)} finding(s), risk tally {risk}.")
    for f in findings[:6]:
        print(f"    [{f['weight']}] {f['signal']:<22} {f['says']}")
        print(f"         seen in: {', '.join(f['seen_in'])}")
    if ai:
        print("\n  AI second opinion (gateway):")
        for ln in ai.strip().splitlines()[:4]:
            print(f"    {ln}")
    print(f"\n  Report: {out / 'triage-report.md'}")
    print(f"  The actions these warrant (approve-gated):  ./securax hunt act {run['id']}")
    return 0


def remediation_plan(pack: dict, findings: list[dict]) -> list[dict]:
    """Turn the fired findings into an ordered, approve-gated remediation plan. An action is proposed only when the
    findings it addresses (its `for` rule ids) actually fired — or always, if it names no `for`. Deterministic: ordered by
    the weight of the findings that justify each step, so the most-supported containment comes first. Each step stays a
    human decision behind ./securax approve; this drafts, it never acts."""
    by_weight = {f["id"]: f["weight"] for f in findings}
    fired = set(by_weight)
    plan = []
    for act in pack.get("actions", []):
        need = act.get("for")
        hits = sorted(set(need) & fired) if need else sorted(fired)
        if need and not hits:
            continue                      # the findings this action addresses did not fire — do not propose it
        priority = max((by_weight[i] for i in hits), default=0)
        plan.append({"action": act["action"], "approve": act["approve"], "why": act["why"],
                     "addresses": hits, "priority": priority})
    plan.sort(key=lambda s: s["priority"], reverse=True)
    return plan


def _ai_remediation(pack_name: str, plan: list[dict], findings: list[dict]) -> str | None:
    """Optional: ask the gateway to draft the plan as a short narrative a responder can act on, under the governed rails and
    audit trail. Offline-safe — None without GATEWAY_URL or on error; the deterministic plan is always what is executed."""
    if not os.getenv("GATEWAY_URL") or not plan:
        return None
    try:
        spec = importlib.util.spec_from_file_location("hunt_personas", ROOT / "agents" / "personas.py")
        personas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(personas)
        steps = "\n".join(f"- {s['action']} (addresses {', '.join(s['addresses']) or 'the findings'})" for s in plan)
        sig = "\n".join(f"- [{f['weight']}] {f['signal']}: {f['says']}" for f in findings)
        q = ("You are drafting a short containment-and-recovery plan for a responder after a post-crisis hunt ('"
             + pack_name + "'). The deterministic plan (already ordered, each step a human-approved action) is:\n" + steps
             + "\n\nThe findings behind it:\n" + sig
             + "\n\nIn at most five short lines, put these in the right order for a responder, say the ONE to do first and "
             "why, and name anything that must happen before a restore. Do not add steps that are not above; do not tell "
             "anyone to act without approval.")
        res = personas.ask_agent("negotiation", q, careful=False)
        return res.get("answer")
    except Exception:  # noqa: BLE001
        return None


def cmd_act(a, now: dt.datetime) -> int:
    run = load_run(a.run)
    p = _pack(run["pack"])
    if run.get("state") != "triaged":
        print(f"{run['id']} is not triaged yet. Run:  ./securax hunt triage {run['id']} --input <dir>")
        return 2
    print(f"▶ {run['id']} — remediation plan for '{p['name']}'.")
    print("  AI and the estate DRAFT; a human approves anything that touches an endpoint. Nothing is executed here.\n")
    if not run.get("findings"):
        print("  No findings scored, so no action is proposed. If you hunted by hand and found something, act on that")
        print("  through ./securax approve directly.")
        return 0
    plan = remediation_plan(p, run["findings"])
    for n, s in enumerate(plan, 1):
        print(f"  {n}. {s['action']}   [priority {s['priority']}]")
        print(f"      addresses: {', '.join(s['addresses'])}")
        print(f"      why: {s['why']}")
        print(f"      run, with a human's single-use approval:  ./securax approve {s['approve']} --run {run['id']}")
        print()
    ai = _ai_remediation(p["name"], plan, run["findings"])
    if ai:
        print("  AI-drafted order (through the governed gateway):")
        for ln in ai.strip().splitlines()[:5]:
            print(f"    {ln}")
        print()
    print("  Each ./securax approve grant is single-use, time-boxed and audited. No agent acts on an endpoint on its own.")
    print(f"  Write the post-hunt report:  ./securax hunt report {run['id']}")
    return 0


def cmd_report(a, now: dt.datetime) -> int:
    """A post-hunt report: the findings, the drafted remediation plan, and the approve-gated steps — ready to feed the
    crisis response pack and to turn gaps into lessons. It records what to do; a human still approves each action."""
    run = load_run(a.run)
    p = _pack(run["pack"])
    if run.get("state") != "triaged":
        print(f"{run['id']} is not triaged yet. Run:  ./securax hunt triage {run['id']} --input <dir>")
        return 2
    plan = remediation_plan(p, run["findings"])
    out = runs_dir() / run["id"]
    out.mkdir(parents=True, exist_ok=True)
    md = [f"# Post-hunt report — {run['id']} ({p['name']})", "",
          f"**Scenario:** {run['scenario']}  ·  **Written:** {local(iso(now))}  ·  **Risk tally:** {run.get('risk', 0)}", "",
          "A first pass to focus a human, never a verdict. Every action below is a decision behind `./securax approve`.", "",
          "## Findings", ""]
    if run.get("findings"):
        md += ["| Priority | Signal | What it means | Seen in |", "|---|---|---|---|"]
        md += [f"| {f['weight']} | `{f['signal']}` | {f['says']} | {', '.join(f['seen_in'])} |" for f in run["findings"]]
    else:
        md.append("No rule matched the collected output — widen the pack or hunt by hand; not a clean bill of health.")
    md += ["", "## Remediation plan (ordered, approve-gated)", ""]
    if plan:
        for n, s in enumerate(plan, 1):
            md.append(f"{n}. **{s['action']}** — {s['why']}  \n   addresses {', '.join(s['addresses'])}; "
                      f"run with `./securax approve {s['approve']} --run {run['id']}`")
    else:
        md.append("No action proposed from the findings.")
    ai = _ai_remediation(p["name"], plan, run["findings"])
    if ai:
        md += ["", "## AI-drafted order (through the governed gateway)", "", ai.strip(),
               "", "_A drafted order, not a verdict; a human confirms and approves each step._"]
    md += ["", "## What was done", "",
           "_Record here which steps were approved, by whom, and the outcome — then feed the gaps to "
           "`./securax crisis` (the response pack) and `./securax lessons add`._"]
    (out / "post-hunt-report.md").write_text("\n".join(md) + "\n", "utf-8")
    os.chmod(out / "post-hunt-report.md", 0o600)
    run["state"] = "reported"
    run["reported_at"] = iso(now)
    save_run(run)
    print(f"▶ Wrote the post-hunt report for {run['id']} ({len(plan)} planned step(s)):")
    print(f"    {out / 'post-hunt-report.md'}")
    print("  Feed it to the crisis response pack and turn each gap into a lesson:")
    print(f"    ./securax crisis status      ·      ./securax lessons add \"hunt {run['scenario']}: <what to fix>\"")
    return 0


def _scenario_pack(scenario: str) -> str | None:
    data = packs_lib()["packs"]
    for pid, p in data.items():
        if p["scenario"] == scenario:
            return pid
    return data and next((pid for pid, p in data.items() if p["scenario"] == "any"), None)


def cmd_auto(a, now: dt.datetime) -> int:
    """Post-crisis automation: pick the pack for the scenario, prepare the collector, and triage if results are given."""
    pid = _scenario_pack(a.scenario)
    if not pid:
        print(f"no hunt pack maps to scenario {a.scenario!r}; see ./securax hunt packs")
        return 2
    p = _pack(pid)
    rid = _new_id(now)
    run = {"id": rid, "pack": pid, "name": p["name"], "scenario": a.scenario, "mode": "offline",
           "artifacts": p["artifacts"], "created_at": iso(now), "state": "planned", "findings": [],
           "auto": True}
    save_run(run)
    out = runs_dir() / rid
    _write_collector(run, p, out)
    print(f"▶ Post-crisis hunt auto-prepared for '{a.scenario}': {rid} using pack '{p['name']}'.")
    print(f"    collector → {out}")
    if a.input:
        print()
        return cmd_triage(argparse.Namespace(run=rid, input=a.input), now)
    print(f"  Run the collector (see {out / 'README.md'}), then:  ./securax hunt triage {rid} --input <dir>")
    print("  Collection is read-only on the endpoint; response actions stay behind ./securax approve.")
    return 0


def _notify(msg: str) -> None:
    """Nudge the configured channel, best-effort, from ONE node only (no duplicate nudges, no SPOF)."""
    try:
        spec = importlib.util.spec_from_file_location("resilience", HERE / "resilience.py")
        res = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(res)
        if not res.is_leader():
            return
    except Exception:  # noqa: BLE001
        pass
    try:
        subprocess.run([str(ROOT / "securax"), "notify", "send", msg], capture_output=True, timeout=30)
    except Exception:  # noqa: BLE001
        pass


def _open_crises() -> list[str]:
    """Open crisis requisition runs (vault/crisis-runs) with pending items — a crisis is in progress."""
    cdir = pathlib.Path(os.environ.get("SECURAX_CRISIS_DIR") or (ROOT / "vault" / "crisis-runs"))
    out = []
    if not cdir.exists():
        return out
    for fp in sorted(cdir.glob("CRISIS-*.json")):
        try:
            run = json.loads(fp.read_text("utf-8"))
            items = [i for s in run.get("sections", []) for i in s.get("items", [])]
            if any(i.get("status") == "pending" for i in items):
                out.append(run["id"])
        except Exception:  # noqa: BLE001
            continue
    return out


def cmd_sweep(a, now: dt.datetime) -> int:
    """During/after a crisis, the estate checks that a hunt is being gathered and nudges if not — one node only."""
    open_crises = _open_crises()
    have_hunt = any(r.get("state") in ("planned", "triaged") for r in runs())
    if not open_crises:
        if not a.quiet:
            print("No open crisis — nothing to hunt for right now.")
        return 0
    if have_hunt:
        if not a.quiet:
            print(f"{len(open_crises)} open crisis; a hunt is already prepared.")
        return 0
    msg = (f"SecuRAX hunt — {len(open_crises)} open crisis and no endpoint hunt prepared yet. "
           f"Gather the evidence now:  ./securax hunt auto <scenario>  (scenarios: see ./securax hunt packs)")
    print(msg)
    if a.notify:
        _notify(msg)
    return 1


def cmd_status(a, now: dt.datetime) -> int:
    if a.run:
        run = load_run(a.run)
        print(json.dumps(run, indent=2))
        return 0
    rs = runs()
    if not rs:
        print("No hunt runs yet. Prepare one:  ./securax hunt collector <pack>   (packs: ./securax hunt packs)")
        return 0
    for r in rs:
        tag = {"planned": "collector ready", "triaged": f"triaged · risk {r.get('risk', 0)}"}.get(r["state"], r["state"])
        print(f"  {r['id']}  {r['name']:<34} [{r['scenario']:<13}] {tag}")
    return 0


def fleet_out(a) -> pathlib.Path:
    base = pathlib.Path(getattr(a, "out", "") or os.environ.get("SECURAX_HUNT_FLEET_DIR")
                        or (ROOT / "vault" / "hunt-fleet"))
    base.mkdir(parents=True, exist_ok=True)
    return base


def _mirror() -> str:
    return os.environ.get("SECURAX_HUNT_MIRROR") or "<MIRROR: set SECURAX_HUNT_MIRROR to your internal registry>"


def _fleet_conditions() -> dict:
    """Reuse the growth-map conditions so fleet readiness lines up with ./securax evolve. Best-effort, local."""
    try:
        spec = importlib.util.spec_from_file_location("hunt_evolve", HERE / "evolve.py")
        ev = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ev)
        return ev.conditions()
    except Exception:  # noqa: BLE001
        return {"nodes": 1, "gateway": False, "fleet_server": False, "internal_mirror": bool(os.getenv("SECURAX_HUNT_MIRROR")),
                "teams": False, "load": False, "lost_node": False}


def cmd_fleet_plan(a, now: dt.datetime) -> int:
    cond = _fleet_conditions()
    fl = fleet_lib()
    print("▶ Hunt fleet — mass deployment (the actuated 'organism' rail of ./securax hunt).")
    print("  This GENERATES the deploy artifacts; it provisions nothing. Standing up the server, pushing the client to")
    print("  every endpoint and running a fleet hunt are your approved steps (./securax approve).\n")
    ready = {"a standing server": cond["fleet_server"], "an internal tool mirror (no vendor egress)": cond["internal_mirror"],
             "more than one node": cond["nodes"] > 1, "multi-team governance": cond["teams"]}
    for k, ok in ready.items():
        print(f"    [{'✓' if ok else ' '}] {k}")
    print("\n  Generate, in order:")
    print("    1. the server:        ./securax hunt fleet server")
    print("    2. the client rollout:./securax hunt fleet clients --method gpo|intune|msiexec|ansible   (omit --method for all)")
    print(f"    3. a throttled hunt:  ./securax hunt fleet hunt <pack>   (packs: {', '.join(packs_lib()['packs'])})")
    if not cond["internal_mirror"]:
        print("\n  Set SECURAX_HUNT_MIRROR to your internal registry first, so endpoints pull the binary from you, not a vendor.")
    print(f"\n  {fl['server']['note']}")
    return 0


def cmd_fleet_server(a, now: dt.datetime) -> int:
    fl = fleet_lib()["server"]
    out = fleet_out(a) / "server"
    out.mkdir(parents=True, exist_ok=True)
    lines = ["# Velociraptor fleet server — stand-up steps (run on the always-on node).",
             "# Generated by ./securax hunt fleet server. Review before running; this provisions a control plane.", ""]
    lines += fl["steps"]
    lines += ["", "# RBAC / multi-org:", "# " + fl["rbac"], "", "# No single point of failure:", "# " + fl["note"]]
    (out / "server-setup.sh").write_text("\n".join(lines) + "\n", "utf-8")
    os.chmod(out / "server-setup.sh", 0o700)
    print(f"▶ Wrote the fleet server setup to {out / 'server-setup.sh'}")
    print("  It sets up the frontend, GUI, an admin and the client config. Give the server a standby (it is the control plane).")
    print("  Then roll clients out:  ./securax hunt fleet clients")
    return 0


def cmd_fleet_clients(a, now: dt.datetime) -> int:
    methods = fleet_lib()["methods"]
    want = [a.method] if a.method else list(methods)
    bad = [m for m in want if m not in methods]
    if bad:
        print(f"unknown method(s) {bad}; known: {', '.join(methods)}")
        return 2
    out = fleet_out(a) / "clients"
    out.mkdir(parents=True, exist_ok=True)
    mirror = _mirror()
    ext = {"msiexec": "txt", "gpo": "txt", "intune": "txt", "ansible": "yml"}
    written = []
    for m in want:
        body = methods[m]["template"].replace("<MIRROR>", mirror)
        fp = out / f"deploy-{m}.{ext[m]}"
        fp.write_text(f"# {methods[m]['name']} — {methods[m]['about']}\n# Binaries come from your internal mirror: {mirror}\n\n{body}\n", "utf-8")
        written.append(fp)
    print(f"▶ Wrote client rollout artifact(s) ({len(written)}):")
    for fp in written:
        print(f"    {fp}")
    print("  Each pulls the binary from your internal mirror (no vendor egress) and is hash-pinned.")
    print("  Pushing to endpoints is a consequential action — do it under your change process / ./securax approve.")
    if "set SECURAX_HUNT_MIRROR" in mirror:
        print("  NOTE: set SECURAX_HUNT_MIRROR to your internal registry, then regenerate, so no <MIRROR> placeholder ships.")
    return 0


def cmd_fleet_hunt(a, now: dt.datetime) -> int:
    if not a.pack:
        print("usage: ./securax hunt fleet hunt <pack>   (packs: ./securax hunt packs)")
        return 2
    if a.pack not in packs_lib()["packs"]:
        print(f"no hunt pack {a.pack!r}; see ./securax hunt packs")
        return 2
    p = _pack(a.pack)
    th = fleet_lib()["throttle"]
    out = fleet_out(a) / "hunts"
    out.mkdir(parents=True, exist_ok=True)
    defn = {"name": f"fleet-{a.pack}", "pack": a.pack, "artifacts": p["artifacts"],
            "throttle": {"ops_per_second": th["ops_per_second"], "cpu_limit_percent": th["cpu_limit_percent"],
                         "max_rows": th["max_rows"]},
            "note": "A server-side hunt across the fleet. Throttled so bulk collection does not saturate the server or link."}
    (out / f"fleet-hunt-{a.pack}.json").write_text(json.dumps(defn, indent=1) + "\n", "utf-8")
    cmd = ["# Queue the hunt on the server (review first; this collects across every client):",
           "velociraptor --config server.config.yaml hunts create \\",
           *[f"  --artifact {art} \\" for art in p["artifacts"]],
           f"  --ops_per_sec {th['ops_per_second']} --cpu_limit {th['cpu_limit_percent']}",
           "# Watch it:  velociraptor --config server.config.yaml hunts list"]
    (out / f"fleet-hunt-{a.pack}.sh").write_text("\n".join(cmd) + "\n", "utf-8")
    os.chmod(out / f"fleet-hunt-{a.pack}.sh", 0o700)
    print(f"▶ Wrote a throttled fleet hunt for '{p['name']}':")
    print(f"    {out / f'fleet-hunt-{a.pack}.json'}  ·  {out / f'fleet-hunt-{a.pack}.sh'}")
    print(f"  Throttle: {th['ops_per_second']} ops/s, {th['cpu_limit_percent']}% CPU. {th['note']}")
    print("  Running a fleet-wide hunt is consequential — queue it under your change process / ./securax approve.")
    return 0


def cmd_fleet(a, now: dt.datetime) -> int:
    fn = {"plan": cmd_fleet_plan, "server": cmd_fleet_server, "clients": cmd_fleet_clients, "hunt": cmd_fleet_hunt}
    return fn[a.action](a, now)


def main(argv: list[str] | None = None, now: dt.datetime | None = None) -> int:
    now = now or dt.datetime.now(UTC)
    argv = list(sys.argv[1:] if argv is None else argv)
    # allow `hunt tools accept <id>` as an alias of `hunt accept <id>`
    if len(argv) >= 2 and argv[0] == "tools" and argv[1] == "accept":
        argv = ["accept", *argv[2:]]
    ap = argparse.ArgumentParser(prog="hunt", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    tl = sub.add_parser("tools")
    tl.add_argument("--json", action="store_true")
    ta = sub.add_parser("accept")
    ta.add_argument("id")
    pk = sub.add_parser("packs")
    pk.add_argument("--json", action="store_true")
    pl = sub.add_parser("plan")
    pl.add_argument("pack")
    co = sub.add_parser("collector")
    co.add_argument("pack")
    co.add_argument("--out", default="")
    au = sub.add_parser("auto")
    au.add_argument("scenario")
    au.add_argument("--input", default="")
    tr = sub.add_parser("triage")
    tr.add_argument("run")
    tr.add_argument("--input", default="")
    ac = sub.add_parser("act")
    ac.add_argument("run")
    rp = sub.add_parser("report")
    rp.add_argument("run")
    fl = sub.add_parser("fleet")
    fl.add_argument("action", choices=["plan", "server", "clients", "hunt"])
    fl.add_argument("pack", nargs="?")
    fl.add_argument("--method", default="", choices=["", "msiexec", "gpo", "intune", "ansible"])
    fl.add_argument("--out", default="")
    sw = sub.add_parser("sweep")
    sw.add_argument("--notify", action="store_true")
    sw.add_argument("--quiet", action="store_true")
    stt = sub.add_parser("status")
    stt.add_argument("run", nargs="?")
    a = ap.parse_args(argv)
    fn = {"tools": cmd_tools, "accept": cmd_tools_accept, "packs": cmd_packs, "plan": cmd_plan,
          "collector": cmd_collector, "auto": cmd_auto, "triage": cmd_triage, "act": cmd_act,
          "report": cmd_report, "fleet": cmd_fleet, "sweep": cmd_sweep, "status": cmd_status}[a.cmd]
    return fn(a, now)


if __name__ == "__main__":
    sys.exit(main())
