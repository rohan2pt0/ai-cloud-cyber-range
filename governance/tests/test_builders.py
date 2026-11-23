"""governance/builders.py: the early warning before a builder provider runs out of money. No network."""
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("builders", ROOT / "governance" / "builders.py")
builders = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builders)

DAY = 86400
T0 = 1_800_000_000


def ok(why="fine"):
    return {"ok": True, "why": why}


def out(why="Monthly limit reached"):
    return {"ok": False, "why": why}


def test_all_ok(tmp_path):
    line = builders.check({"gocode": ok(), "openrouter": ok("credit left: $9.00")}, tmp_path / "s.json", T0)
    assert line == "Builders: all 2 providers can build."


def test_out_under_a_day_is_amber(tmp_path):
    st = tmp_path / "s.json"
    builders.check({"gocode": out()}, st, T0)
    line = builders.check({"gocode": out()}, st, T0 + 3600)
    assert not line.startswith("RED") and "gocode" in line and "Monthly limit reached" in line


def test_out_over_a_day_is_red_with_one_action(tmp_path):
    st = tmp_path / "s.json"
    ans = {"gocode": out(), "openrouter": out("credit left: $0.10"), "gemini": out("quota"), "zed": out("x")}
    builders.check(ans, st, T0)
    line = builders.check(ans, st, T0 + 25 * 3600)
    assert line.startswith("RED")
    assert "turn on Go Extra Usage, or wait for the monthly reset" in line
    assert "buy OpenRouter credit" in line
    assert "check the Google AI Studio key or its free quota" in line
    assert "check its key" in line


def test_recovery_clears_the_clock(tmp_path):
    st = tmp_path / "s.json"
    builders.check({"gocode": out()}, st, T0)
    builders.check({"gocode": ok()}, st, T0 + DAY)
    line = builders.check({"gocode": out()}, st, T0 + 2 * DAY)
    assert not line.startswith("RED")


def test_credit_falling_warns_a_week_ahead(tmp_path):
    st = tmp_path / "s.json"
    for i, left in enumerate((10.0, 8.0, 6.0)):
        line = builders.check({"openrouter": ok(f"credit left: ${left:.2f}")}, st, T0 + i * DAY)
    assert "runs out in about 3 days" in line and not line.startswith("RED")


def test_credit_plenty_is_quiet(tmp_path):
    st = tmp_path / "s.json"
    for i, left in enumerate((100.0, 99.0, 98.0)):
        line = builders.check({"openrouter": ok(f"credit left: ${left:.2f}")}, st, T0 + i * DAY)
    assert line == "Builders: all 1 providers can build."


def test_no_key_is_never_red(tmp_path):
    st = tmp_path / "s.json"
    for why in ("Bearer placeholder", "401 unauthorized", "no key"):
        builders.check({"gemini": out(why)}, st, T0)
        line = builders.check({"gemini": out(why)}, st, T0 + 3 * DAY)
        assert "not checked here (no key)" in line and not line.startswith("RED")


def test_samples_are_bounded_and_state_is_written(tmp_path):
    st = tmp_path / "s.json"
    for i in range(90):
        builders.check({"openrouter": ok("credit left: $50.00")}, st, T0 + i * DAY)
    data = json.loads(st.read_text())
    assert len(data["samples"]["openrouter"]) <= 60
    assert builders.last_line(st)


def test_last_line_missing_or_damaged(tmp_path):
    assert builders.last_line(tmp_path / "none.json") is None
    (tmp_path / "bad.json").write_text("{")
    assert builders.last_line(tmp_path / "bad.json") is None
