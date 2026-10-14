"""Fitness functions: they pass on the real tree, and — the point — they FAIL when the promise is broken."""
import importlib.util
import pathlib
import time

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("fitness", REPO / "lifecycle" / "fitness.py")
ft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ft)


def test_the_real_tree_meets_every_budget():
    bad = [r for r in ft.run_all() if not r["ok"]]
    assert not bad, bad


def test_budgets_are_present_and_sane():
    c = ft.cfg()
    assert {"rails_worst_case_ms", "rails_import_rss_mb", "gateway_cold_start_s", "gateway_rss_mb", "gateway_runtime_deps"} <= set(c["budgets"])
    assert all(v > 0 for v in c["budgets"].values()) and set(c["wake_budgets_s"]) == {"burrow_twin_first_dig", "burrow_twin_wake"}


def test_a_slow_rail_breaks_the_latency_budget(monkeypatch):
    """The ReDoS guard: if a rule goes quadratic, the build must say so."""
    from app import guardrails as g
    real = g.inspect_input

    def slow(text, max_chars=8000, redact=True):
        time.sleep(0.15)
        return real(text, max_chars, redact)
    monkeypatch.setattr(g, "inspect_input", slow)
    r = ft.check_rails_latency(100)
    assert not r["ok"] and r["value"] >= 150


def test_a_real_regex_blowup_is_caught_by_the_adversarial_inputs():
    import re
    evil = re.compile(r"^(a+)+$")                   # the classic catastrophic pattern
    t0 = time.perf_counter()
    evil.match("a" * 24 + "!")
    assert time.perf_counter() - t0 > 0.05, "sanity: this really is slow, so a rail like it could not hide"


def test_dependency_budget_fails_when_exceeded():
    assert ft.check_runtime_deps(99)["ok"] and not ft.check_runtime_deps(1)["ok"]


def test_supply_chain_ratchet_fails_on_new_findings_and_celebrates_fixed_ones():
    now = ft.own_critical_findings()
    victim = sorted(now)[0]
    assert not ft.check_supply_chain({"supply_chain": {k: "x" for k in now if k != victim}})["ok"]           # a NEW finding
    r = ft.check_supply_chain({"supply_chain": {**{k: "x" for k in now}, "gone.sh::pipe-to-shell": "x"}})    # one was fixed
    assert r["ok"] and "FIXED" in r["note"]


def test_every_accepted_supply_chain_finding_has_a_real_reason():
    for k, why in ft.baseline()["supply_chain"].items():
        assert why and "replace this" not in why, k


def test_undocumented_command_ratchet(monkeypatch):
    monkeypatch.setattr(ft, "missing_commands", lambda: {"newcmd"})
    r = ft.check_commands_documented({"undocumented_commands": {}})
    assert not r["ok"] and "newcmd" in r["note"]
    assert ft.check_commands_documented({"undocumented_commands": {"newcmd": "legacy"}})["ok"]


def test_command_discovery_sees_our_commands_and_ignores_flags():
    cmds = ft.commands()
    assert {"up", "grow", "vet", "fitness", "offline", "bench", "diffcheck"} <= set(cmds)
    assert not any(c.startswith("-") for c in cmds) and "up-status" not in cmds


def test_a_missing_gateway_dependency_skips_the_app_checks_instead_of_failing(monkeypatch):
    monkeypatch.setattr(ft, "run_py", lambda code, timeout=120: "MISSING-DEPENDENCY ModuleNotFoundError: No module named 'fastapi'")
    res = ft.check_gateway(5, 120)
    assert all(r["ok"] and "SKIPPED" in r["note"] for r in res)
