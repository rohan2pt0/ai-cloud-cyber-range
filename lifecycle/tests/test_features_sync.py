"""tools/features_sync.py: one features.json written everywhere, facts counted from the code, and a feature whose command or guide
does not exist is refused. Runs against the real repository (read-only) plus synthetic inputs."""
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("features_sync", ROOT / "tools" / "features_sync.py")
fs = importlib.util.module_from_spec(_s)
_s.loader.exec_module(fs)


def test_the_real_repository_is_current_and_every_feature_resolves():
    assert fs.problems() == []
    stale = [p for p, text in fs.outputs().items() if p.read_text("utf-8") != text]
    assert stale == [], "run: python3 tools/features_sync.py"
    data = fs.load()
    assert any(f["id"] == "cyber-range" and f["open"]["cmd"] == "./securax exercise" for f in data["features"])


def test_a_feature_with_a_missing_command_guide_or_group_is_refused():
    data = fs.load()
    bad = dict(data["features"][0], id="ghost", command="no-such-command", doc="securax/99-NOPE.md", group="Nowhere")
    probs = fs.problems({"groups": data["groups"], "features": data["features"] + [bad, dict(bad)]})
    text = " | ".join(probs)
    assert "no-such-command does not exist" in text and "99-NOPE.md does not exist" in text and "not in groups" in text and "used twice" in text


def test_facts_fill_every_marker_and_leave_unknown_ones_alone():
    f = fs.facts()
    assert int(f["journeys"]) > 0 and f["tests"].endswith("+") and int(f["frameworks"]) >= 6
    text = "a <!-- fact:journeys -->1<!-- /fact --> b <!-- fact:unknown -->7<!-- /fact -->"
    out = fs.put_facts(text, f)
    assert f"<!-- fact:journeys -->{f['journeys']}<!-- /fact -->" in out and "<!-- fact:unknown -->7<!-- /fact -->" in out


def test_the_command_center_data_carries_light_guide_and_command():
    js = fs.hub_js(fs.load())
    data = json.loads(js.split("=", 1)[1].rstrip().rstrip(";"))
    rng = next(f for f in data["features"] if f["id"] == "cyber-range")
    assert rng["light"] in ("green", "amber", "red") and rng["guide"].endswith("/securax/79-EXERCISE-RANGE/") and rng["port"] == 8097
