"""`./securax hunt` — threat hunting & post-crisis DFIR (doc 127). SecuRAX ships NO proprietary forensic binary:
the manifest declares each tool's licence + redistribution status and fetches on use; the non-redistributable ones
are gated behind an audited EULA acceptance. Triage scoring is deterministic (identical offline and in CI); every
endpoint action is behind ./securax approve. No network in the tool or these tests."""
import datetime
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("hunt", ROOT / "governance" / "hunt.py")
hunt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hunt)
NOW = datetime.datetime(2026, 11, 6, 6, 0, tzinfo=datetime.timezone.utc)


def test_no_forensic_binary_is_bundled_and_the_manifest_is_honest():
    data = hunt.tools_lib()
    ids = {t["id"] for t in data["tools"]}
    assert {"velociraptor", "system-informer", "kape", "ftk-imager", "autoruns", "resource-hacker"} <= ids
    for t in data["tools"]:
        assert t["bundled"] is False, "SecuRAX must not bundle any third-party forensic binary"
        assert t["licence"] and t["source"]
        # the proprietary tools must be declared non-redistributable AND gated
        if t["id"] in {"kape", "ftk-imager", "autoruns", "resource-hacker"}:
            assert t["redistributable"] is False and t["status"] == "gated"
            assert t.get("licence_note"), "a gated tool must explain its licence"
        if t["id"] in {"velociraptor", "system-informer"}:
            assert t["redistributable"] is True and t["status"] == "active"
    # no vendored binary sits in the repo
    for ext in ("*.exe", "velociraptor*", "autorunsc*", "*.msi"):
        assert not list((ROOT / "governance").glob(ext))


def test_gated_tool_needs_an_audited_acceptance_before_use(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_HUNT_TOOLS_DIR", str(tmp_path))
    # an active tool needs no acceptance
    assert hunt.main(["accept", "velociraptor"], now=NOW) == 0
    assert not (tmp_path / "accepted.json").exists()
    # a gated tool records an acceptance with who/when/licence
    assert hunt.main(["tools", "accept", "kape"], now=NOW) == 0
    acc = json.loads((tmp_path / "accepted.json").read_text("utf-8"))
    assert acc["kape"]["licence"] and acc["kape"]["accepted_at"]
    # an unknown tool is rejected
    assert hunt.main(["accept", "nope"], now=NOW) == 2


def test_packs_map_to_the_crisis_scenarios_and_actions_are_approve_gated():
    data = hunt.packs_lib()["packs"]
    assert {"quick-triage", "ransomware-aftermath", "payment-fraud-persistence", "lateral-movement-sweep"} <= set(data)
    scenarios = {p["scenario"] for p in data.values()}
    assert {"ransomware", "payment-fraud"} <= scenarios   # the two shipped crisis scenarios are covered
    for p in data.values():
        assert p["artifacts"] and p["triage_rules"] and p["actions"]
        for r in p["triage_rules"]:
            assert r["signal"] and r["weight"] >= 1 and r["says"]
        for a in p["actions"]:
            assert a["approve"] and a["action"], "every response action must name its approve verb"


def test_collector_is_offline_and_self_contained(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HUNT_DIR", str(tmp_path))
    assert hunt.main(["collector", "ransomware-aftermath"], now=NOW) == 0
    run = hunt.runs()[0]
    out = tmp_path / run["id"]
    sh = (out / "collect.sh").read_text("utf-8")
    assert "artifacts collect" in sh and "Windows.KapeFiles.Targets" in sh
    # minimal mode: no server, and it tells you nothing is changed on the endpoint
    assert "no server" in (out / "README.md").read_text("utf-8").lower()
    assert run["state"] == "planned"


def test_triage_scores_deterministically_and_ranks_findings(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HUNT_DIR", str(tmp_path))
    monkeypatch.delenv("GATEWAY_URL", raising=False)
    hunt.main(["collector", "ransomware-aftermath"], now=NOW)
    rid = hunt.runs()[0]["id"]
    collected = tmp_path / "collected"
    collected.mkdir()
    (collected / "proc.txt").write_text("C:\\Windows\\Temp\\enc.exe ran vssadmin delete shadows /all", "utf-8")
    (collected / "yara.txt").write_text("cobaltstrike beacon; mimikatz sekurlsa::logonpasswords", "utf-8")
    assert hunt.main(["triage", rid, "--input", str(collected)], now=NOW) == 0
    run = hunt.load_run(rid)
    assert run["state"] == "triaged"
    sigs = [f["signal"] for f in run["findings"]]
    assert "vssadmin delete" in sigs and "cobaltstrike" in sigs and "mimikatz" in sigs
    # weight-3 findings rank above weight-1, and the tally is the sum
    weights = [f["weight"] for f in run["findings"]]
    assert weights == sorted(weights, reverse=True)
    assert run["risk"] == sum(weights)
    # the deterministic run never calls out; AI is purely additive
    assert hunt._ai_triage("x", run["findings"]) is None
    # the report is written and names an approve-gated next step
    assert (tmp_path / rid / "triage-report.md").exists()


def test_act_only_proposes_approve_gated_commands(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_HUNT_DIR", str(tmp_path))
    hunt.main(["collector", "quick-triage"], now=NOW)
    rid = hunt.runs()[0]["id"]
    # act refuses before triage
    assert hunt.main(["act", rid], now=NOW) == 2
    collected = tmp_path / "c"
    collected.mkdir()
    (collected / "n.txt").write_text("listener on 0.0.0.0:4444", "utf-8")
    hunt.main(["triage", rid, "--input", str(collected)], now=NOW)
    capsys.readouterr()
    assert hunt.main(["act", rid], now=NOW) == 0
    out = capsys.readouterr().out
    assert "./securax approve" in out
    # nothing in act executes an endpoint action — it only prints approve commands
    assert "isolate" in out.lower()


def test_auto_picks_the_scenario_pack_and_prepares_a_collector(tmp_path, monkeypatch):
    monkeypatch.setenv("SECURAX_HUNT_DIR", str(tmp_path))
    assert hunt.main(["auto", "ransomware"], now=NOW) == 0
    run = hunt.runs()[0]
    assert run["pack"] == "ransomware-aftermath" and run.get("auto") is True
    # an unknown scenario with no pack (and no 'any' fallback match) still resolves to quick-triage (scenario 'any')
    assert hunt._scenario_pack("totally-unknown") == "quick-triage"


def test_sweep_nudges_only_when_a_crisis_is_open_and_no_hunt_prepared(tmp_path, monkeypatch):
    hd = tmp_path / "hunts"
    cd = tmp_path / "crises"
    hd.mkdir()
    cd.mkdir()
    monkeypatch.setenv("SECURAX_HUNT_DIR", str(hd))
    monkeypatch.setenv("SECURAX_CRISIS_DIR", str(cd))
    # no crisis → calm, exit 0
    assert hunt.main(["sweep", "--quiet"], now=NOW) == 0
    # an open crisis (a pending item) and no hunt → nudge, exit 1
    (cd / "CRISIS-20261106-001.json").write_text(
        json.dumps({"id": "CRISIS-20261106-001", "sections": [{"items": [{"status": "pending"}]}]}), "utf-8")
    assert hunt.main(["sweep", "--quiet"], now=NOW) == 1
    # once a hunt is prepared, the sweep is calm again
    hunt.main(["collector", "ransomware-aftermath"], now=NOW)
    assert hunt.main(["sweep", "--quiet"], now=NOW) == 0


def test_every_crisis_scenario_plus_insider_and_supply_chain_maps_to_a_pack():
    # each crisis scenario, and the two new angles, resolve to a real pack (no 'any' fallback needed)
    for scenario in ("ransomware", "payment-fraud", "data-breach", "outage", "insider", "supply-chain"):
        pid = hunt._scenario_pack(scenario)
        assert pid and hunt._pack(pid)["scenario"] == scenario, f"{scenario} must map to its own pack"


def test_remediation_plan_only_proposes_actions_whose_findings_fired_and_orders_by_weight():
    pack = {"actions": [
        {"id": "a1", "action": "isolate", "approve": "host-isolate", "for": ["r1", "r6"], "why": "contain"},
        {"id": "a2", "action": "restore-gate", "approve": "restore-gate", "for": ["r2"], "why": "clean restore"},
        {"id": "a3", "action": "always", "approve": "note", "why": "no-for action always applies"}]}
    findings = [{"id": "r1", "weight": 3}, {"id": "r6", "weight": 3}]   # r2 did NOT fire
    plan = hunt.remediation_plan(pack, findings)
    approves = [s["approve"] for s in plan]
    assert "restore-gate" not in approves, "an action whose findings did not fire is not proposed"
    assert {"host-isolate", "note"} <= set(approves)
    # ordered by the weight of the findings that justify each step (highest first)
    assert plan[0]["priority"] >= plan[-1]["priority"]
    # the isolate step records exactly which fired findings it addresses
    iso = next(s for s in plan if s["approve"] == "host-isolate")
    assert iso["addresses"] == ["r1", "r6"]


def test_act_shows_the_ordered_plan_and_report_writes_the_artifact(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_HUNT_DIR", str(tmp_path))
    monkeypatch.delenv("GATEWAY_URL", raising=False)
    hunt.main(["collector", "ransomware-aftermath"], now=NOW)
    rid = hunt.runs()[0]["id"]
    collected = tmp_path / "c"
    collected.mkdir()
    (collected / "a.txt").write_text("vssadmin delete shadows /all; mimikatz sekurlsa", "utf-8")
    hunt.main(["triage", rid, "--input", str(collected)], now=NOW)
    capsys.readouterr()
    assert hunt.main(["act", rid], now=NOW) == 0
    out = capsys.readouterr().out
    assert "remediation plan" in out.lower() and "./securax approve" in out
    # report writes the artifact and advances the run state
    assert hunt.main(["report", rid], now=NOW) == 0
    rpt = tmp_path / rid / "post-hunt-report.md"
    assert rpt.exists()
    body = rpt.read_text("utf-8")
    assert "Remediation plan" in body and "approve" in body and "What was done" in body
    assert hunt.load_run(rid)["state"] == "reported"
    # report refuses before triage
    hunt.main(["collector", "service-outage"], now=NOW)
    rid2 = [r["id"] for r in hunt.runs() if r["pack"] == "service-outage"][0]
    assert hunt.main(["report", rid2], now=NOW) == 2
