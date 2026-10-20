"""`./securax storage --auto`, the unattended storage policy: it removes only what can be rebuilt, folds old exercise data
into totals, and tells the phone only when the disk is still short afterwards."""
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("storage", ROOT / "governance" / "storage.py")
st = importlib.util.module_from_spec(_s)
_s.loader.exec_module(st)
sys.path.insert(0, str(ROOT))
from exercise import engine, scenario  # noqa: E402


def test_only_unused_old_versions_of_our_own_images_are_removed():
    imgs = [{"Repository": "securax-exercise-gamebox", "Tag": "aaa", "ID": "1"},            # current
            {"Repository": "securax-exercise-gamebox", "Tag": "bbb", "ID": "2"},            # old, unused: goes
            {"Repository": "securax-exercise-gamebox", "Tag": "ccc", "ID": "3"},            # old, but a stopped range still uses it
            {"Repository": "postgres", "Tag": "16-alpine", "ID": "4"}]                      # third-party: never
    assert st.superseded(imgs, {"securax-exercise-gamebox:ccc"}, {"securax-exercise-gamebox": "aaa"}) == ["securax-exercise-gamebox:bbb"]
    assert st.superseded(imgs, set(), {}) == []                                           # current version unknown: keep everything


def test_auto_folds_exercise_data_and_alerts_only_when_still_short(tmp_path, monkeypatch):
    home = tmp_path / "ex"
    engine.Game.create(home / "EX-1", team=4)
    g = engine.Game(home / "EX-1")
    g.start()
    rows = scenario.checks(g.scenario())
    for _ in range(1445):
        g.db.execute("INSERT INTO checks (round, ts, team, host, zone, service, kind, ok, detail) VALUES (?,?,?,?,?,?,?,?,?)",
                     (_ + 1, 0, 4, rows[0]["host"], rows[0]["zone"], rows[0]["service"], "service", 1, "ok"))
    g.set_meta("round", "1445")
    monkeypatch.setenv("SECURAX_EXERCISE_HOME", str(home))
    sent = []
    healthy = {"docker": False, "disk": {"free_pct": 55.0}}
    monkeypatch.setattr(st, "measure", lambda **k: healthy)
    out = st.auto(healthy, notify=sent.append)
    assert out == ["exercise data: 5 old check results folded into totals"] and sent == []
    short = {"docker": False, "disk": {"free_pct": 4.0}}
    monkeypatch.setattr(st, "measure", lambda **k: short)
    out = st.auto(short, notify=sent.append)
    assert out[-1].startswith("ALERT: Only 4.0%") and len(sent) == 1 and "doc 80" in sent[0]
