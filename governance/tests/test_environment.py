"""Set-and-forget environment changes: reverse each struggle into the ONE best change, with one-time steps (doc 112)."""
import importlib.util
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("environment", REPO / "governance" / "environment.py")
env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(env)


def test_every_entry_is_one_best_change_with_one_time_steps():
    # best-default + shape-environment: one obvious change each, enforced by a one-time setting, never a wall of options.
    for c in env.CATALOG:
        assert c["struggle"] and c["change"] and c["why"], f"{c['id']} must name the struggle, the one change and why"
        assert c["set_once"] and all(c["set_once"].values()), f"{c['id']} must give concrete one-time steps"


def test_every_entry_has_a_wheel_domain_and_an_if_then_plan():
    # the Olympic levers made structural: a Wheel-of-Life domain and an if-then implementation intention on every entry.
    for c in env.CATALOG:
        assert c.get("domain"), f"{c['id']} must name its Wheel-of-Life area"
        assert c.get("if_then", "").lower().startswith("if "), f"{c['id']} must carry an 'If ... then ...' plan"


def test_covers_the_worst_day_struggles_and_the_wheel():
    # worst-day + the Wheel of Life: reverse the hard cases AND cover each major life area, not just easy ones.
    ids = {c["id"] for c in env.CATALOG}
    for needed in ("focus", "phone", "money", "bills", "debt", "routine", "social", "reading", "move", "career", "space", "rest"):
        assert needed in ids, f"missing a reversal for {needed!r}"


def test_filtering_by_struggle_returns_only_those():
    got = env.for_struggles(["focus", "debt"])
    assert {c["id"] for c in got} == {"focus", "debt"}


def test_filtering_by_wheel_domain_word():
    # a domain word (e.g. a weak 'finances' spoke) returns every change in that area — the wheel-to-fix mapping.
    got = {c["id"] for c in env.for_struggles(["finances"])}
    assert got == {"money", "bills", "debt"}


def test_no_struggle_named_returns_all():
    assert len(env.for_struggles([])) == len(env.CATALOG)


def test_unknown_struggle_is_ignored_not_an_error():
    assert env.for_struggles(["nonsense-tag"]) == []      # named something, matched nothing — handled, not crashed


def test_json_is_valid_for_the_life_os_screen(capsys):
    env.main(["--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["catalog"] and len(out["catalog"]) == len(env.CATALOG)


def test_default_run_prints_the_set_once_steps(capsys):
    env.main([])
    out = capsys.readouterr().out
    assert "Set it once" in out and "grey" in out.lower()
