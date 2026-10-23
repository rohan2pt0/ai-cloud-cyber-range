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


def test_covers_the_worst_day_struggles():
    # worst-day: the catalog must actually reverse the hard cases the owner named, not just easy ones.
    ids = {c["id"] for c in env.CATALOG}
    for needed in ("focus", "phone", "money", "bills", "debt", "routine", "social", "reading"):
        assert needed in ids, f"missing a reversal for {needed!r}"


def test_filtering_by_struggle_returns_only_those():
    got = env.for_struggles(["focus", "debt"])
    assert {c["id"] for c in got} == {"focus", "debt"}


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
