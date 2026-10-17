"""`./securax ai`: a reason is required to stop, the switch is written atomically in the form the gateway reads, every action is
logged, and the inventory flags what the RBI MRM draft expects (validation, re-validation, explainability, 10-year records)."""
import datetime as dt
import importlib.util
import json
import pathlib

import pytest

_s = importlib.util.spec_from_file_location("aicontrol", pathlib.Path(__file__).resolve().parent.parent / "aicontrol.py")
ac = importlib.util.module_from_spec(_s)
_s.loader.exec_module(ac)
_k = importlib.util.spec_from_file_location("killswitch", pathlib.Path(__file__).resolve().parents[2] / "apps/llm-gateway/app/killswitch.py")
ks = importlib.util.module_from_spec(_k)
_k.loader.exec_module(ks)


def test_stop_needs_a_reason_and_the_gateway_reads_what_the_cli_writes(tmp_path):
    ctl, log = tmp_path / "ai-control.json", tmp_path / "log.jsonl"
    with pytest.raises(SystemExit):
        ac.stop("all", "  ", "ciso", ctl, log)
    ac.stop("bank-assistant", "bias found in validation", "ciso", ctl, log)
    assert ks.stopped("bank-assistant", ctl)["reason"] == "bias found in validation" and ks.stopped("other", ctl) is None
    ac.stop("all", "incident", "ciso", ctl, log)
    assert ks.stopped("other", ctl)["scope"] == "all"
    ac.resume("all", "ciso", ctl, log)
    ac.resume("bank-assistant", "ciso", ctl, log)
    assert ks.stopped("bank-assistant", ctl) is None
    acts = [json.loads(x)["action"] for x in log.read_text().splitlines()]
    assert acts == ["stop", "stop", "resume", "resume"]


def test_inventory_flags_what_the_draft_expects(tmp_path):
    reg = tmp_path / "r.yaml"
    reg.write_text("""models:
  - {id: ok, risk_tier: high, owner: a, use_case: chat, approved: true, explainability: cites sources, validated: 2026-01-01}
  - {id: stale, risk_tier: high, owner: a, approved: true, explainability: x, validated: 2024-01-01}
  - {id: blackbox, risk_tier: high, owner: a, approved: true, validated: 2026-01-01}
  - {id: never, risk_tier: limited, owner: a, approved: true}
decommissioned:
  - {id: old-scorer, risk_tier: high, decommissioned: 2026-03-31}
""")
    rows = {r["id"]: r for r in ac.inventory(dt.date(2026, 10, 17), reg)}
    assert rows["ok"]["problems"] == [] and rows["ok"]["revalidate_by"] == "2027-01-01"
    assert "re-validation overdue (para 30)" in rows["stale"]["problems"]
    assert "no explainability statement (para 54)" in rows["blackbox"]["problems"]
    assert "not validated (para 29)" in rows["never"]["problems"]
    assert rows["old-scorer"]["retain_until"] == "2036-03-31"


def test_the_shipped_registry_is_clean():
    assert all(not r["problems"] for r in ac.inventory())


def test_an_extension_needs_a_reason_and_applies_to_this_day_or_month_only(tmp_path):
    ctl, log = tmp_path / "ai-control.json", tmp_path / "log.jsonl"
    with pytest.raises(SystemExit):
        ac.extend("day", 1000, "", "me", path=ctl, logp=log)
    with pytest.raises(SystemExit):
        ac.extend("week", 1000, "x", "me", path=ctl, logp=log)
    ac.extend("day", 1000, "old", "me", today=dt.date(2026, 10, 1), path=ctl, logp=log)
    d = ac.extend("month", 5000, "release crunch", "me", today=dt.date(2026, 10, 17), path=ctl, logp=log)
    assert [(e["period"], e["for"]) for e in d["budget_extensions"]] == [("month", "2026-10")]     # yesterday's day-extension is gone
    assert "budget-extend-month" in log.read_text()


def test_a_model_served_but_not_listed_and_a_model_changed_since_validation_are_flagged(tmp_path):
    reg = tmp_path / "r.yaml"
    reg.write_text("""models:
  - {id: a, model: m-v2, validated_model: m-v1, served_as: [chat-a], risk_tier: limited, owner: o, use_case: u, approved: true, validated: 2026-10-01}
""")
    rows = {r["id"]: r for r in ac.inventory(dt.date(2026, 10, 17), reg, live=["chat-a", "shadow-model"])}
    assert "changed since validation (para 42)" in rows["a"]["problems"]
    assert rows["shadow-model"]["problems"] == ["in use at the gateway but not in the inventory (para 21)"]
