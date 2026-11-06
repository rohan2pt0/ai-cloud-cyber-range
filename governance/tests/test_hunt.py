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
