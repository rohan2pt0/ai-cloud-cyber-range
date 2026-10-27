"""Tests for ./securax insight (doc 115): aimed at a goal you set, one durable idea a week, never repeating."""
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ins = _load("securax_insight_t", "governance/insight.py")
CORPUS = ins.corpus()


def _state(wheel=None, okrs=None):
    sov = {"wheel": wheel or {}, "okrs": okrs or []}
    return {"payload": {"sovS": json.dumps(sov)}, "meta": {}}


def _okr(obj, progress):
    # one key result carrying the given progress, so okr_progress() == progress.
    return {"o": obj, "krs": [{"t": "", "v": progress}]}


# ── the corpus is well-formed ─────────────────────────────────────────────────────────────────────────

def test_every_idea_is_complete_and_actionable():
    ids = set()
    doms = set(CORPUS["domains"])
    for i in CORPUS["ideas"]:
        assert i["id"] not in ids, f"duplicate idea id {i['id']}"
        ids.add(i["id"])
        assert i["domain"] in doms, f"{i['id']} has unknown domain {i['domain']}"
        for field in ("title", "idea", "source", "action"):
            assert i.get(field), f"{i['id']} is missing {field}"


def test_every_theme_has_several_ideas():
    # a theme with no ideas would make pick() fall back to the whole corpus; every declared theme must be usable.
    for dom in CORPUS["domains"]:
        n = sum(1 for i in CORPUS["ideas"] if i["domain"] == dom)
        assert n >= 3, f"theme {dom} has only {n} ideas"


# ── aiming ──────────────────────────────────────────────────────────────────────────────────────────

def test_aim_prefers_the_lowest_progress_matching_okr():
    # two OKRs match themes; the one with LOWER progress wins, and its theme is chosen.
    st = _state(okrs=[_okr("Mature our threat detection and incident response", 0.8),
                      _okr("Grow and lead the security team, hire two engineers", 0.1)])
    a = ins.aim(st, 0, CORPUS["domains"])
    assert a["basis"] == "okr"
    assert a["domain"] == "leadership"  # the hiring/lead goal, which is further behind
    assert "lead the security team" in a["goal"]


def test_aim_ignores_okrs_that_match_no_theme_and_falls_to_wheel():
    st = _state(wheel={"money": 3, "growth": 7, "career": 8},
                okrs=[_okr("Plan the family holiday to Kerala", 0.0)])
    a = ins.aim(st, 0, CORPUS["domains"])
    assert a["basis"] == "wheel"
    assert a["domain"] == "money"  # lowest themed wheel area


def test_aim_rotates_when_nothing_scored_or_themed():
    # no okrs, and the only scored wheel area maps to no theme (health) -> rotate, and it varies by week.
    st = _state(wheel={"health": 2})
    doms = list(CORPUS["domains"])
    seen_domains = set()
    for wk in range(len(doms)):
        a = ins.aim(st, wk * ins.WEEK, CORPUS["domains"])
        assert a["basis"] == "rotate"
        seen_domains.add(a["domain"])
    assert seen_domains == set(doms), "rotation should cover every theme across the weeks"


def test_aim_never_raises_on_empty_state():
    for st in (None, {}, {"payload": {}}, {"payload": {"sovS": "not json"}}):
        a = ins.aim(st, 0, CORPUS["domains"])
        assert a["basis"] == "rotate"  # nothing to aim at -> still produces a theme


# ── non-repeating ─────────────────────────────────────────────────────────────────────────────────────

def test_seen_ledger_never_repeats_until_theme_exhausted():
    pool = [i for i in CORPUS["ideas"] if i["domain"] == "money"]
    seen = []
    served = []
    for _ in range(len(pool)):
        got = ins.pick("money", CORPUS["ideas"], 0, seen)
        assert got["id"] not in served, "an idea repeated before the theme was exhausted"
        assert not got["cycled"]
        served.append(got["id"])
        seen.append(got["id"])
    assert set(served) == {i["id"] for i in pool}
    # theme now exhausted -> the next pick signals a restart rather than erroring.
    again = ins.pick("money", CORPUS["ideas"], 0, seen)
    assert again["cycled"] is True


def test_pick_rotates_by_week_when_ledger_unavailable():
    # seen=None models an unreadable ledger; the idea must still vary week to week (no sticking).
    got = {ins.pick("thinking", CORPUS["ideas"], wk * ins.WEEK, None)["id"]
           for wk in range(sum(1 for i in CORPUS["ideas"] if i["domain"] == "thinking"))}
    assert len(got) > 1, "a broken ledger must still rotate, not stick on one idea"


# ── end to end ────────────────────────────────────────────────────────────────────────────────────────

def test_build_aims_at_the_okr_and_carries_a_concrete_action():
    st = _state(okrs=[_okr("Make my money unshakeable, build the emergency fund", 0.2)])
    p = ins.build(now=0, state=st, seen=[], _corpus=CORPUS)
    assert p["aim"]["basis"] == "okr"
    assert p["aim"]["domain"] == "money"
    assert p["idea"]["domain"] == "money"
    assert p["idea"]["action"]
    msg = ins.short(p)
    assert p["idea"]["action"] in msg and p["idea"]["source"] in msg


def test_short_and_report_never_crash_in_any_basis():
    states = [
        _state(okrs=[_okr("Lead the team and delegate better", 0.3)]),      # okr
        _state(wheel={"growth": 2, "career": 9}),                            # wheel
        _state(wheel={"fun": 1}),                                            # rotate
        None,                                                                # rotate
    ]
    for st in states:
        p = ins.build(now=0, state=st, seen=[], _corpus=CORPUS)
        assert ins.short(p)
        lines = []
        ins.report(p, say=lines.append)
        assert any("Do this week" in ln for ln in lines)


def test_main_exits_zero(monkeypatch, capsys):
    monkeypatch.setattr(ins, "build", lambda **k: {
        "aim": {"basis": "rotate", "domain": "thinking"},
        "idea": dict(CORPUS["ideas"][0], cycled=False),
        "theme": "x", "at": 0})
    assert ins.main([]) == 0
    assert ins.main(["--json"]) == 0
