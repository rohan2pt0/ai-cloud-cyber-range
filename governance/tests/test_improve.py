"""governance/improve.py (doc 112): one weekly nudge aimed at the Wheel-of-Life area you rated lowest. It reads the
synced Life OS wheel (the sovS blob), picks the single lowest-scored area, and gives one set-and-forget lever for it,
rotated weekly. It is honest when nothing is scored, and every area maps to a real lever so a nudge is always possible."""
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


im = _load("securax_improve_t", "governance/improve.py")
env = _load("securax_env_t", "governance/environment.py")


def _state(wheel):
    # the Life OS pushes its localStorage; the app state (incl. the wheel) rides in the sovS key as a JSON string
    return {"payload": {"sovS": json.dumps({"wheel": wheel, "okrs": []})}, "meta": {}}


def test_the_lowest_scored_area_is_chosen_and_zero_or_missing_areas_are_ignored():
    scores = im.wheel_scores(_state({"career": 8, "money": 3, "health": 6, "fun": 0}))
    assert scores == {"career": 8, "money": 3, "health": 6}, "a 0 means 'not scored', not 'the worst'"
    w = im.weakest(scores)
    assert w["key"] == "money" and w["label"] == "Finances" and w["domain"] == "finances" and w["score"] == 3


def test_every_wheel_area_maps_to_a_real_lever_so_a_nudge_is_always_possible():
    for _key, label, domain in im.WHEEL:
        assert env.for_struggles([domain]), f"the {label} area ({domain}) must map to at least one environment lever"


def test_the_lever_rotates_week_to_week_for_an_area_with_several():
    # Finances has several levers (money, bills, debt); two different weeks should not be stuck on the same one.
    fin = env.for_struggles(["finances"])
    assert len(fin) >= 2
    picks = {im.lever_for("finances", wk)["id"] for wk in range(len(fin) * 2)}
    assert len(picks) >= 2, "the weekly lever should rotate, not repeat the same change forever"


def test_build_aims_at_the_weakest_area_with_a_concrete_lever():
    p = im.build(now=1_800_000_000.0, state=_state({"career": 9, "money": 7, "growth": 2, "health": 5}))
    assert p["known"] and p["area"]["key"] == "growth" and p["area"]["domain"] == "personal growth"
    assert p["lever"] and p["lever"]["set_once"], "a concrete, set-once lever is attached"
    msg = im.short(p)
    assert "Personal Growth" in msg and "If-then:" in msg and "Set it once:" in msg
    assert "2/10" in msg


def test_an_unscored_wheel_is_honest_and_points_to_the_check_in():
    p = im.build(now=1_800_000_000.0, state=_state({}))
    assert p["known"] is False
    assert "quarterly check-in" in im.short(p).lower()


def test_json_and_report_do_not_crash_on_an_unscored_wheel(capsys):
    im.report(im.build(now=1_800_000_000.0, state=_state({})))
    out = capsys.readouterr().out
    assert "Wheel of Life" in out or "quarterly check-in" in out.lower()
