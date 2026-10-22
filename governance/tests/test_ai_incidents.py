"""AI incident runbooks (doc 105, G11): every kind names how you notice it, how to contain it with commands that exist, what
evidence to keep, and only regulators that are loaded; --kind starts those clocks and prints the runbook; the AI tabletop's
machine checks pass on this checkout. Case data here is fake."""
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load(name, rel):
    s = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


inc = _load("securax_incident_ai_t", "governance/incident.py")
ct = _load("securax_continuity_ai_t", "governance/continuity.py")
KINDS = json.loads((ROOT / "governance" / "ai-incidents.json").read_text("utf-8"))["kinds"]
CLI = (ROOT / "securax").read_text("utf-8")


def test_the_four_kinds_are_complete_and_name_only_real_commands_and_regulators():
    assert {k["id"] for k in KINDS} == {"ai-jailbreak", "ai-data-leak", "ai-abuse", "ai-poisoned-document"}
    regs = {f.stem for f in (ROOT / "governance" / "regulators").glob("*.json")}
    for k in KINDS:
        assert k["signs"] and k["contain"] and k["evidence"], k["id"]
        assert set(k["regulators"]) <= regs, k["id"]
        for line in k["contain"] + k["evidence"]:
            for cmd in re.findall(r"\./securax (\S+)", line):
                assert re.search(rf"^  {re.escape(cmd)}\)", CLI, re.M), f"{k['id']}: ./securax {cmd} is not a command"


def test_opening_an_ai_data_leak_starts_its_clocks_and_prints_the_runbook(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path))
    assert inc.main(["open", "Fake leak", "--kind", "ai-data-leak", "--regulators", "rbi-nbfc"]) == 0
    out = capsys.readouterr().out
    assert "cert-in, dpdp, rbi-nbfc" in out and "Contain it:" in out and "ai stop all" in out
    case = json.loads(next(tmp_path.glob("INC-*.jsonl")).read_text().splitlines()[0])
    assert case["data"]["kind"] == "ai-data-leak" and case["data"]["regulators"] == ["cert-in", "dpdp", "rbi-nbfc"]


def test_a_kind_with_no_default_clock_opens_nothing_and_says_so(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SECURAX_INCIDENT_DIR", str(tmp_path))
    assert inc.main(["open", "Fake abuse", "--kind", "ai-abuse"]) == 0
    assert "no reporting clock starts by default" in capsys.readouterr().out and not list(tmp_path.glob("INC-*"))
    assert inc.main(["open", "x", "--kind", "ai-nonsense"]) == 2


def test_the_ai_tabletop_checks_pass_on_this_checkout():
    assert ct.tabletop_check("killswitch")[0] is True
    assert ct.tabletop_check("ai_clock")[0] is True
    ex = next(x for x in ct.exercises() if x["id"] == "ai-incident")
    assert {i.get("check") for i in ex["injects"]} >= {"killswitch", "ai_clock"}
